from __future__ import annotations

import math
import uuid

from fastapi import HTTPException
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.business.model import BusinessCreateRequest, BusinessCreateResponse, BusinessUpdateRequest
from app.business.repository import BusinessRepository
from app.business.schemas import BusinessCreate, BusinessRead, BusinessUpdate
from app.business_user.repository import create_business_user
from app.business_user.schemas import BusinessUserCreate
from app.role.model import OWNER_ROLE_CODE
from app.role.repository import read_role_by_code
from app.user.repository import read_user_by_id
from app.user.schemas import UserRead
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest, Pagination
from app.utility.service_deps import readable_service, writable_service
from app.utility.token import create_customer_token


def _parse_business_id(business_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(business_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Business not found") from exc


def _parse_user_id(user_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc


def _to_business_update(payload: BusinessUpdateRequest) -> BusinessUpdate:
    data = payload.model_dump(exclude_unset=True)
    user_id = data.pop("user_id", None)
    if user_id is not None:
        data["user_id"] = uuid.UUID(str(user_id))
    return BusinessUpdate(**data)


def _to_read(row) -> BusinessRead:
    return BusinessRead.model_validate(row)


class BusinessService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BusinessRepository(session)

    async def create(
        self,
        business: BusinessCreateRequest,
        user_id: str,
    ) -> BusinessCreateResponse:
        parsed_user_id = _parse_user_id(user_id)
        user_row = await read_user_by_id(self._session, parsed_user_id)
        if user_row is None:
            raise HTTPException(status_code=404, detail="User not found")

        existing_business = await self._repo.read_by_user_id(parsed_user_id)
        if existing_business:
            raise HTTPException(
                status_code=409,
                detail="You already have a business. Each user can only create one business.",
            )

        owner_role = await read_role_by_code(self._session, OWNER_ROLE_CODE)
        if owner_role is None:
            raise HTTPException(
                status_code=404,
                detail="Owner role not found. Please ensure standard roles are created.",
            )

        try:
            created_business = await self._repo.create(
                BusinessCreate(
                    user_id=parsed_user_id,
                    name=business.name,
                    description=business.description,
                    logo=business.logo,
                ),
            )
            await create_business_user(
                self._session,
                BusinessUserCreate(
                    business_id=created_business.id,
                    user_id=parsed_user_id,
                    role_id=owner_role.id,
                ),
            )
        except IntegrityError as exc:
            raise HTTPException(
                status_code=409,
                detail="You already have a business. Each user can only create one business.",
            ) from exc

        new_token = create_customer_token(UserRead.model_validate(user_row), has_business=True)
        return BusinessCreateResponse(token=new_token)

    async def update(self, id: str, business: BusinessUpdateRequest) -> Response:
        parsed_id = _parse_business_id(id)
        try:
            updated = await self._repo.update(parsed_id, _to_business_update(business))
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Business constraint violation") from exc
        if updated is None:
            raise HTTPException(status_code=404, detail="Business not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_business_id(id)
        deleted = await self._repo.delete(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Business not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[BusinessRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count()
        rows = await self._repo.list(offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[BusinessRead](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id(self, id: str) -> BaseResponse[BusinessRead]:
        parsed_id = _parse_business_id(id)
        row = await self._repo.read_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Business not found")
        return BaseResponse[BusinessRead](status_code=200, message="Successful", data=_to_read(row))

    async def read_by_user_id(self, user_id: str) -> BaseResponse[BusinessRead | None]:
        parsed_user_id = _parse_user_id(user_id)
        row = await self._repo.read_by_user_id(parsed_user_id)
        return BaseResponse[BusinessRead | None](
            status_code=200,
            message="Successful",
            data=_to_read(row) if row else None,
        )


class WritableBusinessService(writable_service(BusinessService)):
    pass


class ReadableBusinessService(readable_service(BusinessService)):
    pass

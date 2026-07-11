from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.business_user.model import BusinessUserCreateRequest, BusinessUserUpdateRequest
from app.business_user.repository import BusinessUserRepository
from app.business_user.schemas import BusinessUserCreate, BusinessUserRead, BusinessUserUpdate
from app.user.repository import UserRepository
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.revocation import revoke_user_active_session
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Mapping not found") from exc


def _to_create(payload: BusinessUserCreateRequest) -> BusinessUserCreate:
    return BusinessUserCreate(
        business_id=uuid.UUID(str(payload.business_id)),
        user_id=uuid.UUID(str(payload.user_id)),
        role_id=uuid.UUID(str(payload.role_id)),
    )


def _to_update(payload: BusinessUserUpdateRequest) -> BusinessUserUpdate:
    data = payload.model_dump(exclude_unset=True)
    for field in ("business_id", "user_id", "role_id"):
        if field in data and data[field] is not None:
            data[field] = uuid.UUID(str(data[field]))
    return BusinessUserUpdate(**data)


def _to_read(row) -> BusinessUserRead:
    return BusinessUserRead.model_validate(row)


class BusinessUserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BusinessUserRepository(session)
        self._user_repo = UserRepository(session)

    async def create(self, mapping: BusinessUserCreateRequest) -> Response:
        await self._repo.create_business_user(_to_create(mapping))
        return Response(status_code=201)

    async def update(self, id: str, mapping: BusinessUserUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        existing = await self._repo.read_business_user_by_id(parsed_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Mapping not found")

        update_data = mapping.model_dump(exclude_unset=True)
        authority_changed = any(
            field in update_data and update_data[field] is not None
            for field in ("role_id", "status")
        )
        updated = await self._repo.update_business_user(parsed_id, _to_update(mapping))
        if updated is None:
            raise HTTPException(status_code=404, detail="Mapping not found")

        if authority_changed:
            await revoke_user_active_session(self._user_repo, existing.user_id)
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        existing = await self._repo.read_business_user_by_id(parsed_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Mapping not found")

        deleted = await self._repo.delete_business_user(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Mapping not found")

        await revoke_user_active_session(self._user_repo, existing.user_id)
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[BusinessUserRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_business_users()
        rows = await self._repo.list_business_users(offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[BusinessUserRead](
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

    async def read_by_id(self, id: str) -> BaseResponse[BusinessUserRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_business_user_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return BaseResponse[BusinessUserRead](
            status_code=200, message="Successful", data=_to_read(row)
        )

    async def read_by_business_id(self, business_id: str) -> BaseResponse[list[BusinessUserRead]]:
        parsed_business_id = _parse_id(business_id)
        rows = await self._repo.read_business_users_by_business_id(parsed_business_id)
        return BaseResponse[list[BusinessUserRead]](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
        )


class WritableBusinessUserService(writable_service(BusinessUserService)):
    pass


class ReadableBusinessUserService(readable_service(BusinessUserService)):
    pass

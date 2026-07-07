from __future__ import annotations

import math
import uuid

from fastapi import HTTPException
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError

from app.business.model import BusinessCreateRequest, BusinessCreateResponse, BusinessUpdateRequest
from app.business.repository import (
    create_business,
    list_businesses,
    read_business_by_id,
    read_business_by_user_id,
    delete_business,
    update_business,
    count_businesses,
)
from app.business.schemas import BusinessCreate, BusinessRead, BusinessUpdate
from app.business_user.repository import create_business_user
from app.business_user.schemas import BusinessUserCreate
from app.role.model import OWNER_ROLE_CODE
from app.role.repository import read_role_by_code
from app.user.query import read_by_id_query as read_user_by_id_query
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest, Pagination
from app.utility.postgres import get_sessionmaker
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


async def create_service(business: BusinessCreateRequest, user_id: str) -> BusinessCreateResponse:
    user_record = await read_user_by_id_query(user_id)
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")

    parsed_user_id = _parse_user_id(user_id)

    async with get_sessionmaker()() as session:
        existing_business = await read_business_by_user_id(session, parsed_user_id)
        if existing_business:
            raise HTTPException(
                status_code=409,
                detail="You already have a business. Each user can only create one business.",
            )

        owner_role = await read_role_by_code(session, OWNER_ROLE_CODE)
        if owner_role is None:
            raise HTTPException(
                status_code=404,
                detail="Owner role not found. Please ensure standard roles are created.",
            )

        try:
            created_business = await create_business(
                session,
                BusinessCreate(
                    user_id=parsed_user_id,
                    name=business.name,
                    description=business.description,
                    logo=business.logo,
                ),
            )
            await create_business_user(
                session,
                BusinessUserCreate(
                    business_id=created_business.id,
                    user_id=parsed_user_id,
                    role_id=owner_role.id,
                ),
            )
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail="You already have a business. Each user can only create one business.",
            ) from exc

    new_token = create_customer_token(user_record, has_business=True)
    return BusinessCreateResponse(token=new_token)


async def update_service(id: str, business: BusinessUpdateRequest) -> Response:
    parsed_id = _parse_business_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_business(session, parsed_id, _to_business_update(business))
        if updated is None:
            raise HTTPException(status_code=404, detail="Business not found")
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(status_code=409, detail="Business constraint violation") from exc
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    parsed_id = _parse_business_id(id)
    async with get_sessionmaker()() as session:
        deleted = await delete_business(session, parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Business not found")
        await session.commit()
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[BusinessRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_businesses(session)
        rows = await list_businesses(session, offset=offset, limit=size)

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


async def read_by_id_service(id: str) -> BaseResponse[BusinessRead]:
    parsed_id = _parse_business_id(id)
    async with get_sessionmaker()() as session:
        row = await read_business_by_id(session, parsed_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return BaseResponse[BusinessRead](status_code=200, message="Successful", data=_to_read(row))


async def read_by_user_id_service(user_id: str) -> BaseResponse[BusinessRead | None]:
    parsed_user_id = _parse_user_id(user_id)
    async with get_sessionmaker()() as session:
        row = await read_business_by_user_id(session, parsed_user_id)
    return BaseResponse[BusinessRead | None](
        status_code=200,
        message="Successful",
        data=_to_read(row) if row else None,
    )

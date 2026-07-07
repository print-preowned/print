from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response

from app.business_user.model import BusinessUserCreateRequest, BusinessUserUpdateRequest
from app.business_user.repository import (
    create_business_user,
    list_business_users,
    read_business_user_by_id,
    read_business_users_by_business_id,
    soft_delete_business_user,
    update_business_user,
    count_business_users,
)
from app.business_user.schemas import BusinessUserCreate, BusinessUserRead, BusinessUserUpdate
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest, Pagination
from app.utility.postgres import get_sessionmaker


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


async def create_service(mapping: BusinessUserCreateRequest) -> Response:
    async with get_sessionmaker()() as session:
        await create_business_user(session, _to_create(mapping))
        await session.commit()
    return Response(status_code=201)


async def update_service(id: str, mapping: BusinessUserUpdateRequest) -> Response:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_business_user(session, parsed_id, _to_update(mapping))
        if updated is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        await session.commit()
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_business_user(session, parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Mapping not found")
        await session.commit()
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[BusinessUserRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_business_users(session)
        rows = await list_business_users(session, offset=offset, limit=size)

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


async def read_by_id_service(id: str) -> BaseResponse[BusinessUserRead]:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_business_user_by_id(session, parsed_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return BaseResponse[BusinessUserRead](status_code=200, message="Successful", data=_to_read(row))


async def read_by_business_id_service(business_id: str) -> BaseResponse[list[BusinessUserRead]]:
    parsed_business_id = _parse_id(business_id)
    async with get_sessionmaker()() as session:
        rows = await read_business_users_by_business_id(session, parsed_business_id)
    return BaseResponse[list[BusinessUserRead]](
        status_code=200,
        message="Successful",
        data=[_to_read(row) for row in rows],
    )

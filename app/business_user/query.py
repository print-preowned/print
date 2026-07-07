from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.business_user.model import BusinessUserCreateRequest, BusinessUserUpdateRequest
from app.business_user.repository import (
    create_business_user,
    list_business_users,
    read_business_user_by_id,
    read_business_user_by_user_id,
    read_business_users_by_business_id,
    soft_delete_business_user,
    update_business_user,
    count_business_users,
)
from app.business_user.schemas import BusinessUserCreate, BusinessUserRead, BusinessUserUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_business_user_update(payload: BusinessUserUpdateRequest) -> BusinessUserUpdate:
    data = payload.model_dump(exclude_unset=True)
    for field in ("business_id", "user_id", "role_id"):
        if field in data and data[field] is not None:
            data[field] = uuid.UUID(str(data[field]))
    return BusinessUserUpdate(**data)


def _to_create(payload: BusinessUserCreateRequest) -> BusinessUserCreate:
    return BusinessUserCreate(
        business_id=uuid.UUID(str(payload.business_id)),
        user_id=uuid.UUID(str(payload.user_id)),
        role_id=uuid.UUID(str(payload.role_id)),
    )


def _to_read(row) -> BusinessUserRead:
    return BusinessUserRead.model_validate(row)


async def create_query(mapping: BusinessUserCreateRequest) -> None:
    async with get_sessionmaker()() as session:
        await create_business_user(session, _to_create(mapping))
        await session.commit()


async def update_query(id: str, mapping: BusinessUserUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_business_user(session, parsed_id, _to_business_user_update(mapping))
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
        return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_business_user(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
        return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[BusinessUserRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_business_users(session)
        rows = await list_business_users(session, offset=offset, limit=size)

    total_pages = math.ceil(total_results / size) if size else 1
    return PaginatedData(
        data=[_to_read(row) for row in rows],
        pagination=Pagination(
            page=page,
            size=size,
            total_pages=total_pages,
            total_results=total_results,
        ),
    )


async def read_by_id_query(id: str) -> BusinessUserRead | None:
    async with get_sessionmaker()() as session:
        row = await read_business_user_by_id(session, _parse_id(id))
    return _to_read(row) if row else None


async def read_by_business_id_query(business_id: str) -> list[BusinessUserRead]:
    async with get_sessionmaker()() as session:
        rows = await read_business_users_by_business_id(session, _parse_id(business_id))
    return [_to_read(row) for row in rows]


async def read_one_by_user_id_query(user_id: str) -> BusinessUserRead | None:
    async with get_sessionmaker()() as session:
        row = await read_business_user_by_user_id(session, uuid.UUID(user_id))
    return _to_read(row) if row else None

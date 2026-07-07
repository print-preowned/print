from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.platform_user.model import PlatformUserCreateRequest, PlatformUserUpdateRequest
from app.platform_user.repository import (
    create_platform_user,
    list_platform_users,
    read_active_by_privilege_set_id,
    read_platform_user_by_id,
    read_platform_user_by_user_id,
    soft_delete_platform_user,
    update_platform_user,
    count_platform_users,
)
from app.platform_user.schemas import PlatformUserCreate, PlatformUserRead, PlatformUserUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PlatformUserRead:
    return PlatformUserRead.model_validate(row)


def _to_create(payload: PlatformUserCreateRequest) -> PlatformUserCreate:
    return PlatformUserCreate(
        user_id=uuid.UUID(str(payload.user_id)),
        platform_privilege_set_id=uuid.UUID(str(payload.platform_privilege_set_id)),
        status=payload.status,
    )


def _to_update(payload: PlatformUserUpdateRequest) -> PlatformUserUpdate:
    data = payload.model_dump(exclude_unset=True)
    if "platform_privilege_set_id" in data and data["platform_privilege_set_id"] is not None:
        data["platform_privilege_set_id"] = uuid.UUID(str(data["platform_privilege_set_id"]))
    return PlatformUserUpdate(**data)


async def create_query(platform_user: PlatformUserCreateRequest) -> None:
    async with get_sessionmaker()() as session:
        await create_platform_user(session, _to_create(platform_user))
        await session.commit()


async def update_query(id: str, platform_user: PlatformUserUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_platform_user(session, parsed_id, _to_update(platform_user))
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_platform_user(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[PlatformUserRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_platform_users(session)
        rows = await list_platform_users(session, offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> PlatformUserRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_platform_user_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_user_id_query(user_id: str) -> PlatformUserRead | None:
    parsed_user_id = _parse_id(user_id)
    async with get_sessionmaker()() as session:
        row = await read_platform_user_by_user_id(session, parsed_user_id)
    return _to_read(row) if row else None


async def read_active_by_privilege_set_id_query(
    privilege_set_id: str,
) -> PlatformUserRead | None:
    parsed_id = _parse_id(privilege_set_id)
    async with get_sessionmaker()() as session:
        row = await read_active_by_privilege_set_id(session, parsed_id)
    return _to_read(row) if row else None

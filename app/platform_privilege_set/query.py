from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.platform_privilege_set.model import (
    PlatformPrivilegeSetCreateRequest,
    PlatformPrivilegeSetUpdateRequest,
)
from app.platform_privilege_set.repository import (
    create_platform_privilege_set,
    list_platform_privilege_sets,
    read_platform_privilege_set_by_id,
    read_platform_privilege_set_by_name,
    read_platform_privilege_sets_by_ids,
    soft_delete_platform_privilege_set,
    update_platform_privilege_set,
    count_platform_privilege_sets,
)
from app.platform_privilege_set.schemas import (
    PlatformPrivilegeSetCreate,
    PlatformPrivilegeSetRead,
    PlatformPrivilegeSetUpdate,
)
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PlatformPrivilegeSetRead:
    return PlatformPrivilegeSetRead.model_validate(row)


async def create_query(platform_privilege_set: PlatformPrivilegeSetCreateRequest) -> None:
    payload = PlatformPrivilegeSetCreate.model_validate(platform_privilege_set.model_dump())
    async with get_sessionmaker()() as session:
        await create_platform_privilege_set(session, payload)
        await session.commit()


async def update_query(
    id: str,
    platform_privilege_set: PlatformPrivilegeSetUpdateRequest,
) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_platform_privilege_set(
            session,
            parsed_id,
            PlatformPrivilegeSetUpdate.model_validate(
                platform_privilege_set.model_dump(exclude_unset=True)
            ),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_platform_privilege_set(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(
    params: ParamRequest,
    *,
    exclude_names: list[str] | None = None,
) -> PaginatedData[PlatformPrivilegeSetRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_platform_privilege_sets(session, exclude_names=exclude_names)
        rows = await list_platform_privilege_sets(
            session,
            offset=offset,
            limit=size,
            exclude_names=exclude_names,
        )

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


async def read_by_id_query(id: str) -> PlatformPrivilegeSetRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_platform_privilege_set_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_ids_query(ids: list[str]) -> list[PlatformPrivilegeSetRead]:
    if not ids:
        return []
    parsed_ids = [_parse_id(value) for value in ids]
    async with get_sessionmaker()() as session:
        rows = await read_platform_privilege_sets_by_ids(session, parsed_ids)
    return [_to_read(row) for row in rows]


async def read_by_name_query(name: str) -> PlatformPrivilegeSetRead | None:
    async with get_sessionmaker()() as session:
        row = await read_platform_privilege_set_by_name(session, name)
    return _to_read(row) if row else None

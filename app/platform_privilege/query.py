from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.platform_privilege.model import (
    PlatformPrivilegeCreateRequest,
    PlatformPrivilegeUpdateRequest,
)
from app.platform_privilege.repository import (
    create_platform_privilege,
    list_platform_privileges,
    read_platform_privilege_by_code,
    read_platform_privilege_by_id,
    soft_delete_platform_privilege,
    update_platform_privilege,
    count_platform_privileges,
)
from app.platform_privilege.schemas import PlatformPrivilegeCreate, PlatformPrivilegeRead, PlatformPrivilegeUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PlatformPrivilegeRead:
    return PlatformPrivilegeRead.model_validate(row)


async def create_query(platform_privilege: PlatformPrivilegeCreateRequest) -> None:
    payload = PlatformPrivilegeCreate.model_validate(platform_privilege.model_dump())
    async with get_sessionmaker()() as session:
        await create_platform_privilege(session, payload)
        await session.commit()


async def update_query(id: str, platform_privilege: PlatformPrivilegeUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_platform_privilege(
            session,
            parsed_id,
            PlatformPrivilegeUpdate.model_validate(platform_privilege.model_dump(exclude_unset=True)),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_platform_privilege(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[PlatformPrivilegeRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_platform_privileges(session)
        rows = await list_platform_privileges(session, offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> PlatformPrivilegeRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_platform_privilege_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_code_query(code: str) -> PlatformPrivilegeRead | None:
    async with get_sessionmaker()() as session:
        row = await read_platform_privilege_by_code(session, code)
    return _to_read(row) if row else None

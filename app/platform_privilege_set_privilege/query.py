from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.platform_privilege_set_privilege.model import (
    PlatformPrivilegeSetPrivilegeCreateRequest,
    PlatformPrivilegeSetPrivilegeUpdateRequest,
)
from app.platform_privilege_set_privilege.repository import (
    create_platform_privilege_set_privilege,
    list_platform_privilege_set_privileges,
    read_by_privilege_set_and_code,
    read_by_privilege_set_id,
    read_platform_privilege_set_privilege_by_id,
    soft_delete_by_privilege_set_and_code,
    soft_delete_platform_privilege_set_privilege,
    update_platform_privilege_set_privilege,
    count_platform_privilege_set_privileges,
)
from app.platform_privilege_set_privilege.schemas import (
    PlatformPrivilegeSetPrivilegeCreate,
    PlatformPrivilegeSetPrivilegeRead,
    PlatformPrivilegeSetPrivilegeUpdate,
)
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PlatformPrivilegeSetPrivilegeRead:
    return PlatformPrivilegeSetPrivilegeRead.model_validate(row)


async def create_query(mapping: PlatformPrivilegeSetPrivilegeCreateRequest) -> None:
    data = mapping.model_dump()
    data["privilege_set_id"] = uuid.UUID(str(data["privilege_set_id"]))
    payload = PlatformPrivilegeSetPrivilegeCreate.model_validate(data)
    async with get_sessionmaker()() as session:
        await create_platform_privilege_set_privilege(session, payload)
        await session.commit()


async def update_query(
    id: str,
    mapping: PlatformPrivilegeSetPrivilegeUpdateRequest,
) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_platform_privilege_set_privilege(
            session,
            parsed_id,
            PlatformPrivilegeSetPrivilegeUpdate.model_validate(
                mapping.model_dump(exclude_unset=True)
            ),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_platform_privilege_set_privilege(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[PlatformPrivilegeSetPrivilegeRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_platform_privilege_set_privileges(session)
        rows = await list_platform_privilege_set_privileges(session, offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> PlatformPrivilegeSetPrivilegeRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_platform_privilege_set_privilege_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_privilege_set_id_query(
    privilege_set_id: str,
) -> list[PlatformPrivilegeSetPrivilegeRead]:
    parsed_id = _parse_id(privilege_set_id)
    async with get_sessionmaker()() as session:
        rows = await read_by_privilege_set_id(session, parsed_id)
    return [_to_read(row) for row in rows]


async def read_by_privilege_set_and_privilege_query(
    privilege_set_id: str,
    privilege_code: str,
) -> PlatformPrivilegeSetPrivilegeRead | None:
    parsed_id = _parse_id(privilege_set_id)
    async with get_sessionmaker()() as session:
        row = await read_by_privilege_set_and_code(session, parsed_id, privilege_code)
    return _to_read(row) if row else None


async def delete_by_privilege_set_and_privilege_query(
    privilege_set_id: str,
    privilege_code: str,
) -> UpdateResult:
    parsed_id = _parse_id(privilege_set_id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_by_privilege_set_and_code(session, parsed_id, privilege_code)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.role_privilege.model import RolePrivilegeCreateRequest, RolePrivilegeUpdateRequest
from app.role_privilege.repository import (
    count_role_privileges,
    create_role_privilege,
    list_role_privileges,
    read_by_privilege_code,
    read_privilege_codes_by_role_id,
    read_role_privilege_by_id,
    read_role_privilege_by_role_and_code,
    soft_delete_by_role_and_code,
    soft_delete_role_privilege,
    update_role_privilege,
)
from app.role_privilege.schemas import RolePrivilegeCreate, RolePrivilegeRead, RolePrivilegeUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> RolePrivilegeRead:
    return RolePrivilegeRead.model_validate(row)


async def create_query(mapping: RolePrivilegeCreateRequest) -> None:
    payload = RolePrivilegeCreate(
        role_id=_parse_id(mapping.role_id),
        privilege_code=mapping.privilege_code,
    )
    async with get_sessionmaker()() as session:
        await create_role_privilege(session, payload)
        await session.commit()


async def update_query(id: str, mapping: RolePrivilegeUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    update_data = mapping.model_dump(exclude_unset=True)
    if "role_id" in update_data and update_data["role_id"] is not None:
        update_data["role_id"] = _parse_id(update_data["role_id"])

    async with get_sessionmaker()() as session:
        updated = await update_role_privilege(
            session,
            parsed_id,
            RolePrivilegeUpdate.model_validate(update_data),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_role_privilege(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_by_role_and_privilege_query(role_id: str, privilege_code: str) -> UpdateResult:
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_by_role_and_code(
            session,
            _parse_id(role_id),
            privilege_code,
        )
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[RolePrivilegeRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_role_privileges(session)
        rows = await list_role_privileges(session, offset=offset, limit=size)
        data = [_to_read(row) for row in rows]

    total_pages = math.ceil(total_results / size) if size else 1
    return PaginatedData(
        data=data,
        pagination=Pagination(
            page=page,
            size=size,
            total_pages=total_pages,
            total_results=total_results,
        ),
    )


async def read_by_id_query(id: str) -> RolePrivilegeRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_role_privilege_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_role_and_privilege_query(
    role_id: str,
    privilege_code: str,
) -> RolePrivilegeRead | None:
    async with get_sessionmaker()() as session:
        row = await read_role_privilege_by_role_and_code(
            session,
            _parse_id(role_id),
            privilege_code,
        )
    return _to_read(row) if row else None


async def read_by_privilege_code_query(privilege_code: str) -> list[RolePrivilegeRead]:
    async with get_sessionmaker()() as session:
        rows = await read_by_privilege_code(session, privilege_code)
    return [_to_read(row) for row in rows]


async def read_privilege_codes_by_role_id_query(role_id: str) -> list[str]:
    async with get_sessionmaker()() as session:
        return await read_privilege_codes_by_role_id(session, _parse_id(role_id))

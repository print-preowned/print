from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.privilege.model import PrivilegeCreateRequest, PrivilegeUpdateRequest
from app.privilege.repository import PrivilegeRepository
from app.privilege.schemas import PrivilegeCreate, PrivilegeRead, PrivilegeUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PrivilegeRead:
    return PrivilegeRead.model_validate(row)


def _to_create(payload: PrivilegeCreateRequest) -> PrivilegeCreate:
    return PrivilegeCreate.model_validate(
        payload.model_dump(include=set(PrivilegeCreate.model_fields.keys()))
    )


async def create_query(privilege: PrivilegeCreateRequest) -> None:
    async with get_sessionmaker()() as session:
        await PrivilegeRepository(session).create_privilege(_to_create(privilege))
        await session.commit()


async def update_query(id: str, privilege: PrivilegeUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await PrivilegeRepository(session).update_privilege(
            parsed_id,
            PrivilegeUpdate.model_validate(privilege.model_dump(exclude_unset=True)),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await PrivilegeRepository(session).soft_delete_privilege(parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_by_code_query(code: str) -> UpdateResult:
    async with get_sessionmaker()() as session:
        deleted = await PrivilegeRepository(session).soft_delete_privilege_by_code(code)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[PrivilegeRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await PrivilegeRepository(session).count_privileges()
        rows = await PrivilegeRepository(session).list_privileges(offset=offset, limit=size)
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


async def read_by_id_query(id: str) -> PrivilegeRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await PrivilegeRepository(session).read_privilege_by_id(parsed_id)
    return _to_read(row) if row else None


async def read_by_code_query(code: str) -> PrivilegeRead | None:
    async with get_sessionmaker()() as session:
        row = await PrivilegeRepository(session).read_privilege_by_code(code)
    return _to_read(row) if row else None


async def read_by_module_name_query(module_name: str) -> list[PrivilegeRead]:
    async with get_sessionmaker()() as session:
        rows = await PrivilegeRepository(session).read_privileges_by_module_name(module_name)
    return [_to_read(row) for row in rows]

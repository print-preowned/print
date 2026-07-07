from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.role.model import RoleCreateRequest, RoleUpdateRequest
from app.role.repository import (
    count_roles,
    create_role,
    list_roles,
    read_role_by_code,
    read_role_by_id,
    soft_delete_role,
    update_role,
)
from app.role.schemas import RoleCreate, RoleRead, RoleUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> RoleRead:
    return RoleRead.model_validate(row)


def _to_create(payload: RoleCreateRequest) -> RoleCreate:
    data = payload.model_dump(include=set(RoleCreate.model_fields.keys()))
    if data.get("code") is None:
        data["code"] = payload.name.upper().replace(" ", "_")
    return RoleCreate.model_validate(data)


async def create_query(role: RoleCreateRequest) -> str:
    async with get_sessionmaker()() as session:
        created = await create_role(session, _to_create(role))
        await session.commit()
        return str(created.id)


async def update_query(id: str, role: RoleUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_role(
            session,
            parsed_id,
            RoleUpdate.model_validate(role.model_dump(exclude_unset=True)),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_role(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[RoleRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_roles(session)
        rows = await list_roles(session, offset=offset, limit=size)
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


async def read_by_id_query(id: str) -> RoleRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_role_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_code_query(code: str) -> RoleRead | None:
    async with get_sessionmaker()() as session:
        row = await read_role_by_code(session, code)
    return _to_read(row) if row else None

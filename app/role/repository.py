from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.role.orm import RoleOrm
from app.role.schemas import RoleCreate, RoleUpdate


async def create_role(session: AsyncSession, payload: RoleCreate) -> RoleOrm:
    role = RoleOrm(**payload.model_dump())
    session.add(role)
    await session.flush()
    return role


async def update_role(
    session: AsyncSession,
    role_id: uuid.UUID,
    payload: RoleUpdate,
) -> RoleOrm | None:
    role = await read_role_by_id(session, role_id)
    if role is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    await session.flush()
    return role


async def soft_delete_role(session: AsyncSession, role_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(RoleOrm)
        .where(RoleOrm.id == role_id, RoleOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(RoleOrm.id)
    )
    return deleted_id is not None


async def read_role_by_id(session: AsyncSession, role_id: uuid.UUID) -> RoleOrm | None:
    return await session.scalar(
        select(RoleOrm).where(RoleOrm.id == role_id, RoleOrm.deleted_at.is_(None))
    )


async def read_role_by_code(session: AsyncSession, code: str) -> RoleOrm | None:
    return await session.scalar(
        select(RoleOrm).where(RoleOrm.code == code, RoleOrm.deleted_at.is_(None))
    )


async def count_roles(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(RoleOrm).where(RoleOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_roles(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[RoleOrm]:
    statement: Select[tuple[RoleOrm]] = (
        select(RoleOrm)
        .where(RoleOrm.deleted_at.is_(None))
        .order_by(RoleOrm.name)
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

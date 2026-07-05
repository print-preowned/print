from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.role.orm import RoleOrm
from app.role.schemas import RoleCreate


async def create_role(session: AsyncSession, payload: RoleCreate) -> RoleOrm:
    role = RoleOrm(**payload.model_dump())
    session.add(role)
    await session.flush()
    return role


async def read_role_by_id(session: AsyncSession, role_id: uuid.UUID) -> RoleOrm | None:
    return await session.scalar(
        select(RoleOrm).where(RoleOrm.id == role_id, RoleOrm.deleted_at.is_(None))
    )


async def read_role_by_code(session: AsyncSession, code: str) -> RoleOrm | None:
    return await session.scalar(
        select(RoleOrm).where(RoleOrm.code == code, RoleOrm.deleted_at.is_(None))
    )

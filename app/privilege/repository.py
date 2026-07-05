from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.privilege.orm import PrivilegeOrm
from app.privilege.schemas import PrivilegeCreate


async def create_privilege(session: AsyncSession, payload: PrivilegeCreate) -> PrivilegeOrm:
    privilege = PrivilegeOrm(**payload.model_dump())
    session.add(privilege)
    await session.flush()
    return privilege


async def read_privilege_by_code(session: AsyncSession, code: str) -> PrivilegeOrm | None:
    return await session.scalar(
        select(PrivilegeOrm).where(
            PrivilegeOrm.code == code,
            PrivilegeOrm.deleted_at.is_(None),
        )
    )

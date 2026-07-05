from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.role_privilege.orm import RolePrivilegeOrm
from app.role_privilege.schemas import RolePrivilegeCreate


async def create_role_privilege(
    session: AsyncSession,
    payload: RolePrivilegeCreate,
) -> RolePrivilegeOrm:
    mapping = RolePrivilegeOrm(**payload.model_dump())
    session.add(mapping)
    await session.flush()
    return mapping


async def read_role_privilege_by_role_and_code(
    session: AsyncSession,
    role_id: uuid.UUID,
    privilege_code: str,
) -> RolePrivilegeOrm | None:
    return await session.scalar(
        select(RolePrivilegeOrm).where(
            RolePrivilegeOrm.role_id == role_id,
            RolePrivilegeOrm.privilege_code == privilege_code,
            RolePrivilegeOrm.deleted_at.is_(None),
        )
    )


async def read_privilege_codes_by_role_id(
    session: AsyncSession,
    role_id: uuid.UUID,
) -> list[str]:
    result = await session.scalars(
        select(RolePrivilegeOrm.privilege_code).where(
            RolePrivilegeOrm.role_id == role_id,
            RolePrivilegeOrm.deleted_at.is_(None),
        )
    )
    return list(result)

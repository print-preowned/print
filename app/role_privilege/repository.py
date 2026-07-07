from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.role_privilege.orm import RolePrivilegeOrm
from app.role_privilege.schemas import RolePrivilegeCreate, RolePrivilegeUpdate


async def create_role_privilege(
    session: AsyncSession,
    payload: RolePrivilegeCreate,
) -> RolePrivilegeOrm:
    mapping = RolePrivilegeOrm(**payload.model_dump())
    session.add(mapping)
    await session.flush()
    return mapping


async def update_role_privilege(
    session: AsyncSession,
    mapping_id: uuid.UUID,
    payload: RolePrivilegeUpdate,
) -> RolePrivilegeOrm | None:
    row = await read_role_privilege_by_id(session, mapping_id)
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    return row


async def soft_delete_role_privilege(session: AsyncSession, mapping_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(RolePrivilegeOrm)
        .where(RolePrivilegeOrm.id == mapping_id, RolePrivilegeOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(RolePrivilegeOrm.id)
    )
    return deleted_id is not None


async def soft_delete_by_role_and_code(
    session: AsyncSession,
    role_id: uuid.UUID,
    privilege_code: str,
) -> bool:
    deleted_id = await session.scalar(
        update(RolePrivilegeOrm)
        .where(
            RolePrivilegeOrm.role_id == role_id,
            RolePrivilegeOrm.privilege_code == privilege_code,
            RolePrivilegeOrm.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(RolePrivilegeOrm.id)
    )
    return deleted_id is not None


async def read_role_privilege_by_id(
    session: AsyncSession,
    mapping_id: uuid.UUID,
) -> RolePrivilegeOrm | None:
    return await session.scalar(
        select(RolePrivilegeOrm).where(
            RolePrivilegeOrm.id == mapping_id,
            RolePrivilegeOrm.deleted_at.is_(None),
        )
    )


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


async def read_by_privilege_code(session: AsyncSession, privilege_code: str) -> list[RolePrivilegeOrm]:
    result = await session.scalars(
        select(RolePrivilegeOrm).where(
            RolePrivilegeOrm.privilege_code == privilege_code,
            RolePrivilegeOrm.deleted_at.is_(None),
        )
    )
    return list(result)


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


async def count_role_privileges(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(RolePrivilegeOrm).where(RolePrivilegeOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_role_privileges(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[RolePrivilegeOrm]:
    statement: Select[tuple[RolePrivilegeOrm]] = (
        select(RolePrivilegeOrm)
        .where(RolePrivilegeOrm.deleted_at.is_(None))
        .order_by(RolePrivilegeOrm.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_privilege.orm import PlatformPrivilegeOrm
from app.platform_privilege.schemas import PlatformPrivilegeCreate, PlatformPrivilegeUpdate


async def create_platform_privilege(
    session: AsyncSession,
    payload: PlatformPrivilegeCreate,
) -> PlatformPrivilegeOrm:
    privilege = PlatformPrivilegeOrm(**payload.model_dump())
    session.add(privilege)
    await session.flush()
    return privilege


async def update_platform_privilege(
    session: AsyncSession,
    privilege_id: uuid.UUID,
    payload: PlatformPrivilegeUpdate,
) -> PlatformPrivilegeOrm | None:
    privilege = await read_platform_privilege_by_id(session, privilege_id)
    if privilege is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(privilege, field, value)
    await session.flush()
    return privilege


async def soft_delete_platform_privilege(session: AsyncSession, privilege_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(PlatformPrivilegeOrm)
        .where(
            PlatformPrivilegeOrm.id == privilege_id,
            PlatformPrivilegeOrm.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(PlatformPrivilegeOrm.id)
    )
    return deleted_id is not None


async def read_platform_privilege_by_id(
    session: AsyncSession,
    privilege_id: uuid.UUID,
) -> PlatformPrivilegeOrm | None:
    return await session.scalar(
        select(PlatformPrivilegeOrm).where(
            PlatformPrivilegeOrm.id == privilege_id,
            PlatformPrivilegeOrm.deleted_at.is_(None),
        )
    )


async def read_platform_privilege_by_code(
    session: AsyncSession,
    code: str,
) -> PlatformPrivilegeOrm | None:
    return await session.scalar(
        select(PlatformPrivilegeOrm).where(
            PlatformPrivilegeOrm.code == code,
            PlatformPrivilegeOrm.deleted_at.is_(None),
        )
    )


async def count_platform_privileges(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count())
        .select_from(PlatformPrivilegeOrm)
        .where(PlatformPrivilegeOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_platform_privileges(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[PlatformPrivilegeOrm]:
    statement: Select[tuple[PlatformPrivilegeOrm]] = (
        select(PlatformPrivilegeOrm)
        .where(PlatformPrivilegeOrm.deleted_at.is_(None))
        .order_by(PlatformPrivilegeOrm.code)
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

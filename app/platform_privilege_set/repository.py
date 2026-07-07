from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_privilege_set.orm import PlatformPrivilegeSetOrm
from app.platform_privilege_set.schemas import PlatformPrivilegeSetCreate, PlatformPrivilegeSetUpdate


async def create_platform_privilege_set(
    session: AsyncSession,
    payload: PlatformPrivilegeSetCreate,
) -> PlatformPrivilegeSetOrm:
    privilege_set = PlatformPrivilegeSetOrm(**payload.model_dump())
    session.add(privilege_set)
    await session.flush()
    return privilege_set


async def update_platform_privilege_set(
    session: AsyncSession,
    privilege_set_id: uuid.UUID,
    payload: PlatformPrivilegeSetUpdate,
) -> PlatformPrivilegeSetOrm | None:
    privilege_set = await read_platform_privilege_set_by_id(session, privilege_set_id)
    if privilege_set is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(privilege_set, field, value)
    await session.flush()
    return privilege_set


async def soft_delete_platform_privilege_set(
    session: AsyncSession,
    privilege_set_id: uuid.UUID,
) -> bool:
    deleted_id = await session.scalar(
        update(PlatformPrivilegeSetOrm)
        .where(
            PlatformPrivilegeSetOrm.id == privilege_set_id,
            PlatformPrivilegeSetOrm.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(PlatformPrivilegeSetOrm.id)
    )
    return deleted_id is not None


async def read_platform_privilege_set_by_id(
    session: AsyncSession,
    privilege_set_id: uuid.UUID,
) -> PlatformPrivilegeSetOrm | None:
    return await session.scalar(
        select(PlatformPrivilegeSetOrm).where(
            PlatformPrivilegeSetOrm.id == privilege_set_id,
            PlatformPrivilegeSetOrm.deleted_at.is_(None),
        )
    )


async def read_platform_privilege_set_by_name(
    session: AsyncSession,
    name: str,
) -> PlatformPrivilegeSetOrm | None:
    return await session.scalar(
        select(PlatformPrivilegeSetOrm).where(
            PlatformPrivilegeSetOrm.name == name,
            PlatformPrivilegeSetOrm.deleted_at.is_(None),
        )
    )


async def read_platform_privilege_sets_by_ids(
    session: AsyncSession,
    privilege_set_ids: list[uuid.UUID],
) -> list[PlatformPrivilegeSetOrm]:
    if not privilege_set_ids:
        return []
    result = await session.scalars(
        select(PlatformPrivilegeSetOrm).where(
            PlatformPrivilegeSetOrm.id.in_(privilege_set_ids),
            PlatformPrivilegeSetOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def count_platform_privilege_sets(
    session: AsyncSession,
    *,
    exclude_names: list[str] | None = None,
) -> int:
    statement = (
        select(func.count())
        .select_from(PlatformPrivilegeSetOrm)
        .where(PlatformPrivilegeSetOrm.deleted_at.is_(None))
    )
    if exclude_names:
        statement = statement.where(PlatformPrivilegeSetOrm.name.notin_(exclude_names))
    total = await session.scalar(statement)
    return int(total or 0)


async def list_platform_privilege_sets(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    exclude_names: list[str] | None = None,
) -> list[PlatformPrivilegeSetOrm]:
    statement: Select[tuple[PlatformPrivilegeSetOrm]] = (
        select(PlatformPrivilegeSetOrm)
        .where(PlatformPrivilegeSetOrm.deleted_at.is_(None))
        .order_by(PlatformPrivilegeSetOrm.name)
        .offset(offset)
        .limit(limit)
    )
    if exclude_names:
        statement = statement.where(PlatformPrivilegeSetOrm.name.notin_(exclude_names))
    result = await session.scalars(statement)
    return list(result)

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_user.orm import PlatformUserOrm
from app.platform_user.schemas import PlatformUserCreate, PlatformUserUpdate


async def create_platform_user(
    session: AsyncSession,
    payload: PlatformUserCreate,
) -> PlatformUserOrm:
    platform_user = PlatformUserOrm(**payload.model_dump())
    session.add(platform_user)
    await session.flush()
    return platform_user


async def update_platform_user(
    session: AsyncSession,
    platform_user_id: uuid.UUID,
    payload: PlatformUserUpdate,
) -> PlatformUserOrm | None:
    platform_user = await read_platform_user_by_id(session, platform_user_id)
    if platform_user is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(platform_user, field, value)
    await session.flush()
    return platform_user


async def soft_delete_platform_user(session: AsyncSession, platform_user_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(PlatformUserOrm)
        .where(
            PlatformUserOrm.id == platform_user_id,
            PlatformUserOrm.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(PlatformUserOrm.id)
    )
    return deleted_id is not None


async def read_platform_user_by_id(
    session: AsyncSession,
    platform_user_id: uuid.UUID,
) -> PlatformUserOrm | None:
    return await session.scalar(
        select(PlatformUserOrm).where(
            PlatformUserOrm.id == platform_user_id,
            PlatformUserOrm.deleted_at.is_(None),
        )
    )


async def read_platform_user_by_user_id(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> PlatformUserOrm | None:
    return await session.scalar(
        select(PlatformUserOrm).where(
            PlatformUserOrm.user_id == user_id,
            PlatformUserOrm.deleted_at.is_(None),
        )
    )


async def read_active_by_privilege_set_id(
    session: AsyncSession,
    privilege_set_id: uuid.UUID,
) -> PlatformUserOrm | None:
    return await session.scalar(
        select(PlatformUserOrm).where(
            PlatformUserOrm.platform_privilege_set_id == privilege_set_id,
            PlatformUserOrm.status == "ACTIVE",
            PlatformUserOrm.deleted_at.is_(None),
        )
    )


async def count_platform_users(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count())
        .select_from(PlatformUserOrm)
        .where(PlatformUserOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_platform_users(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[PlatformUserOrm]:
    statement: Select[tuple[PlatformUserOrm]] = (
        select(PlatformUserOrm)
        .where(PlatformUserOrm.deleted_at.is_(None))
        .order_by(PlatformUserOrm.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

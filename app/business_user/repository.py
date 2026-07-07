from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.business_user.orm import BusinessUserOrm
from app.business_user.schemas import BusinessUserCreate, BusinessUserUpdate


async def create_business_user(
    session: AsyncSession,
    payload: BusinessUserCreate,
) -> BusinessUserOrm:
    mapping = BusinessUserOrm(**payload.model_dump())
    session.add(mapping)
    await session.flush()
    return mapping


async def update_business_user(
    session: AsyncSession,
    business_user_id: uuid.UUID,
    payload: BusinessUserUpdate,
) -> BusinessUserOrm | None:
    mapping = await read_business_user_by_id(session, business_user_id)
    if mapping is None:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(mapping, field, value)
    await session.flush()
    return mapping


async def soft_delete_business_user(session: AsyncSession, business_user_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(BusinessUserOrm)
        .where(BusinessUserOrm.id == business_user_id, BusinessUserOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC))
        .returning(BusinessUserOrm.id)
    )
    return deleted_id is not None


async def read_business_user_by_id(
    session: AsyncSession,
    business_user_id: uuid.UUID,
) -> BusinessUserOrm | None:
    return await session.scalar(
        select(BusinessUserOrm).where(
            BusinessUserOrm.id == business_user_id,
            BusinessUserOrm.deleted_at.is_(None),
        )
    )


async def read_business_user_by_user_id(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> BusinessUserOrm | None:
    return await session.scalar(
        select(BusinessUserOrm).where(
            BusinessUserOrm.user_id == user_id,
            BusinessUserOrm.deleted_at.is_(None),
        )
    )


async def read_business_users_by_business_id(
    session: AsyncSession,
    business_id: uuid.UUID,
) -> list[BusinessUserOrm]:
    result = await session.scalars(
        select(BusinessUserOrm).where(
            BusinessUserOrm.business_id == business_id,
            BusinessUserOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def count_business_users(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count())
        .select_from(BusinessUserOrm)
        .where(BusinessUserOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_business_users(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[BusinessUserOrm]:
    statement: Select[tuple[BusinessUserOrm]] = (
        select(BusinessUserOrm)
        .where(BusinessUserOrm.deleted_at.is_(None))
        .order_by(BusinessUserOrm.created_at)
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

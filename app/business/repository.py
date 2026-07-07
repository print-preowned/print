from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.business.orm import BusinessOrm
from app.business.schemas import BusinessCreate, BusinessUpdate


async def create_business(session: AsyncSession, payload: BusinessCreate) -> BusinessOrm:
    business = BusinessOrm(**payload.model_dump())
    session.add(business)
    await session.flush()
    return business


async def update_business(
    session: AsyncSession,
    business_id: uuid.UUID,
    payload: BusinessUpdate,
) -> BusinessOrm | None:
    business = await read_business_by_id(session, business_id)
    if business is None:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(business, field, value)
    await session.flush()
    return business


async def delete_business(session: AsyncSession, business_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(BusinessOrm)
        .where(BusinessOrm.id == business_id, BusinessOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC))
        .returning(BusinessOrm.id)
    )
    return deleted_id is not None


async def read_business_by_id(session: AsyncSession, business_id: uuid.UUID) -> BusinessOrm | None:
    return await session.scalar(
        select(BusinessOrm).where(
            BusinessOrm.id == business_id,
            BusinessOrm.deleted_at.is_(None),
        )
    )


async def read_business_by_user_id(session: AsyncSession, user_id: uuid.UUID) -> BusinessOrm | None:
    return await session.scalar(
        select(BusinessOrm).where(
            BusinessOrm.user_id == user_id,
            BusinessOrm.deleted_at.is_(None),
        )
    )


async def count_businesses(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(BusinessOrm).where(BusinessOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_businesses(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[BusinessOrm]:
    statement: Select[tuple[BusinessOrm]] = (
        select(BusinessOrm)
        .where(BusinessOrm.deleted_at.is_(None))
        .order_by(BusinessOrm.name)
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

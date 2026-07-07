from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.business_rating.orm import BusinessRatingOrm
from app.business_rating.schemas import BusinessRatingCreate, BusinessRatingUpdate


async def create_business_rating(
    session: AsyncSession,
    payload: BusinessRatingCreate,
) -> BusinessRatingOrm:
    row = BusinessRatingOrm(**payload.model_dump())
    session.add(row)
    await session.flush()
    return row


async def update_business_rating(
    session: AsyncSession,
    rating_id: uuid.UUID,
    payload: BusinessRatingUpdate,
) -> BusinessRatingOrm | None:
    row = await read_business_rating_by_id(session, rating_id)
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    return row


async def soft_delete_business_rating(session: AsyncSession, rating_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(BusinessRatingOrm)
        .where(BusinessRatingOrm.id == rating_id, BusinessRatingOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(BusinessRatingOrm.id)
    )
    return deleted_id is not None


async def read_business_rating_by_id(
    session: AsyncSession,
    rating_id: uuid.UUID,
) -> BusinessRatingOrm | None:
    return await session.scalar(
        select(BusinessRatingOrm).where(
            BusinessRatingOrm.id == rating_id,
            BusinessRatingOrm.deleted_at.is_(None),
        )
    )


async def read_by_business_id(
    session: AsyncSession,
    business_id: uuid.UUID,
) -> list[BusinessRatingOrm]:
    result = await session.scalars(
        select(BusinessRatingOrm).where(
            BusinessRatingOrm.business_id == business_id,
            BusinessRatingOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def count_business_ratings(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count())
        .select_from(BusinessRatingOrm)
        .where(BusinessRatingOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_business_ratings(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[BusinessRatingOrm]:
    statement: Select[tuple[BusinessRatingOrm]] = (
        select(BusinessRatingOrm)
        .where(BusinessRatingOrm.deleted_at.is_(None))
        .order_by(BusinessRatingOrm.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

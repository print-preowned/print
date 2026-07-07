from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.book_rating.orm import BookRatingOrm
from app.book_rating.schemas import BookRatingCreate, BookRatingUpdate


async def create_book_rating(session: AsyncSession, payload: BookRatingCreate) -> BookRatingOrm:
    row = BookRatingOrm(**payload.model_dump())
    session.add(row)
    await session.flush()
    return row


async def update_book_rating(
    session: AsyncSession,
    rating_id: uuid.UUID,
    payload: BookRatingUpdate,
) -> BookRatingOrm | None:
    row = await read_book_rating_by_id(session, rating_id)
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    return row


async def soft_delete_book_rating(session: AsyncSession, rating_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(BookRatingOrm)
        .where(BookRatingOrm.id == rating_id, BookRatingOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(BookRatingOrm.id)
    )
    return deleted_id is not None


async def read_book_rating_by_id(session: AsyncSession, rating_id: uuid.UUID) -> BookRatingOrm | None:
    return await session.scalar(
        select(BookRatingOrm).where(
            BookRatingOrm.id == rating_id,
            BookRatingOrm.deleted_at.is_(None),
        )
    )


async def read_by_book_id(session: AsyncSession, book_id: uuid.UUID) -> list[BookRatingOrm]:
    result = await session.scalars(
        select(BookRatingOrm).where(
            BookRatingOrm.book_id == book_id,
            BookRatingOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def read_by_user_id(session: AsyncSession, user_id: uuid.UUID) -> list[BookRatingOrm]:
    result = await session.scalars(
        select(BookRatingOrm).where(
            BookRatingOrm.user_id == user_id,
            BookRatingOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def count_book_ratings(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(BookRatingOrm).where(BookRatingOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_book_ratings(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[BookRatingOrm]:
    statement: Select[tuple[BookRatingOrm]] = (
        select(BookRatingOrm)
        .where(BookRatingOrm.deleted_at.is_(None))
        .order_by(BookRatingOrm.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

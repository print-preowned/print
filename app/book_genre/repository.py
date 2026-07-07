from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.book_genre.orm import BookGenreOrm
from app.book_genre.schemas import BookGenreCreate, BookGenreUpdate


async def create_book_genre(session: AsyncSession, payload: BookGenreCreate) -> BookGenreOrm:
    row = BookGenreOrm(**payload.model_dump())
    session.add(row)
    await session.flush()
    return row


async def update_book_genre(
    session: AsyncSession,
    mapping_id: uuid.UUID,
    payload: BookGenreUpdate,
) -> BookGenreOrm | None:
    row = await read_book_genre_by_id(session, mapping_id)
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    return row


async def soft_delete_book_genre(session: AsyncSession, mapping_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(BookGenreOrm)
        .where(BookGenreOrm.id == mapping_id, BookGenreOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(BookGenreOrm.id)
    )
    return deleted_id is not None


async def soft_delete_by_book_and_genre(
    session: AsyncSession,
    book_id: uuid.UUID,
    genre_id: uuid.UUID,
) -> bool:
    deleted_id = await session.scalar(
        update(BookGenreOrm)
        .where(
            BookGenreOrm.book_id == book_id,
            BookGenreOrm.genre_id == genre_id,
            BookGenreOrm.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(BookGenreOrm.id)
    )
    return deleted_id is not None


async def read_book_genre_by_id(
    session: AsyncSession,
    mapping_id: uuid.UUID,
) -> BookGenreOrm | None:
    return await session.scalar(
        select(BookGenreOrm).where(
            BookGenreOrm.id == mapping_id,
            BookGenreOrm.deleted_at.is_(None),
        )
    )


async def read_by_book_id(session: AsyncSession, book_id: uuid.UUID) -> list[BookGenreOrm]:
    result = await session.scalars(
        select(BookGenreOrm).where(
            BookGenreOrm.book_id == book_id,
            BookGenreOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def read_by_book_ids(session: AsyncSession, book_ids: list[uuid.UUID]) -> list[BookGenreOrm]:
    if not book_ids:
        return []
    result = await session.scalars(
        select(BookGenreOrm).where(
            BookGenreOrm.book_id.in_(book_ids),
            BookGenreOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def read_by_genre_id(session: AsyncSession, genre_id: uuid.UUID) -> list[BookGenreOrm]:
    result = await session.scalars(
        select(BookGenreOrm).where(
            BookGenreOrm.genre_id == genre_id,
            BookGenreOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def count_book_genres(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(BookGenreOrm).where(BookGenreOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_book_genres(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[BookGenreOrm]:
    statement: Select[tuple[BookGenreOrm]] = (
        select(BookGenreOrm)
        .where(BookGenreOrm.deleted_at.is_(None))
        .order_by(BookGenreOrm.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

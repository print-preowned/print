from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.book.orm import BookOrm
from app.book.schemas import BookCreate, BookUpdate


async def create_book(session: AsyncSession, payload: BookCreate) -> BookOrm:
    book = BookOrm(**payload.model_dump())
    session.add(book)
    await session.flush()
    return book


async def update_book(
    session: AsyncSession,
    book_id: uuid.UUID,
    payload: BookUpdate,
) -> BookOrm | None:
    book = await read_book_by_id(session, book_id)
    if book is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    await session.flush()
    return book


async def soft_delete_book(session: AsyncSession, book_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(BookOrm)
        .where(BookOrm.id == book_id, BookOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(BookOrm.id)
    )
    return deleted_id is not None


async def read_book_by_id(session: AsyncSession, book_id: uuid.UUID) -> BookOrm | None:
    return await session.scalar(
        select(BookOrm).where(BookOrm.id == book_id, BookOrm.deleted_at.is_(None))
    )


async def read_books_by_ids(session: AsyncSession, book_ids: list[uuid.UUID]) -> list[BookOrm]:
    if not book_ids:
        return []
    result = await session.scalars(
        select(BookOrm).where(BookOrm.id.in_(book_ids), BookOrm.deleted_at.is_(None))
    )
    return list(result)


async def count_books(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(BookOrm).where(BookOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_books(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[BookOrm]:
    statement: Select[tuple[BookOrm]] = (
        select(BookOrm)
        .where(BookOrm.deleted_at.is_(None))
        .order_by(BookOrm.title)
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

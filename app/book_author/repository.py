from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.book_author.orm import BookAuthorOrm
from app.book_author.schemas import BookAuthorCreate, BookAuthorUpdate


async def create_book_author(session: AsyncSession, payload: BookAuthorCreate) -> BookAuthorOrm:
    row = BookAuthorOrm(**payload.model_dump())
    session.add(row)
    await session.flush()
    return row


async def update_book_author(
    session: AsyncSession,
    mapping_id: uuid.UUID,
    payload: BookAuthorUpdate,
) -> BookAuthorOrm | None:
    row = await read_book_author_by_id(session, mapping_id)
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    return row


async def soft_delete_book_author(session: AsyncSession, mapping_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(BookAuthorOrm)
        .where(BookAuthorOrm.id == mapping_id, BookAuthorOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(BookAuthorOrm.id)
    )
    return deleted_id is not None


async def soft_delete_by_book_and_author(
    session: AsyncSession,
    book_id: uuid.UUID,
    author_id: uuid.UUID,
) -> bool:
    deleted_id = await session.scalar(
        update(BookAuthorOrm)
        .where(
            BookAuthorOrm.book_id == book_id,
            BookAuthorOrm.author_id == author_id,
            BookAuthorOrm.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(BookAuthorOrm.id)
    )
    return deleted_id is not None


async def read_book_author_by_id(
    session: AsyncSession,
    mapping_id: uuid.UUID,
) -> BookAuthorOrm | None:
    return await session.scalar(
        select(BookAuthorOrm).where(
            BookAuthorOrm.id == mapping_id,
            BookAuthorOrm.deleted_at.is_(None),
        )
    )


async def read_by_book_id(session: AsyncSession, book_id: uuid.UUID) -> list[BookAuthorOrm]:
    result = await session.scalars(
        select(BookAuthorOrm).where(
            BookAuthorOrm.book_id == book_id,
            BookAuthorOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def read_by_book_ids(session: AsyncSession, book_ids: list[uuid.UUID]) -> list[BookAuthorOrm]:
    if not book_ids:
        return []
    result = await session.scalars(
        select(BookAuthorOrm).where(
            BookAuthorOrm.book_id.in_(book_ids),
            BookAuthorOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def read_by_author_id(session: AsyncSession, author_id: uuid.UUID) -> list[BookAuthorOrm]:
    result = await session.scalars(
        select(BookAuthorOrm).where(
            BookAuthorOrm.author_id == author_id,
            BookAuthorOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def count_book_authors(session: AsyncSession) -> int:
    from sqlalchemy import func

    total = await session.scalar(
        select(func.count()).select_from(BookAuthorOrm).where(BookAuthorOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_book_authors(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[BookAuthorOrm]:
    from sqlalchemy import Select

    statement: Select[tuple[BookAuthorOrm]] = (
        select(BookAuthorOrm)
        .where(BookAuthorOrm.deleted_at.is_(None))
        .order_by(BookAuthorOrm.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)

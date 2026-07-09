from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.book.orm import BookOrm
from app.book.schemas import BookCreate, BookUpdate


class BookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_book(self, payload: BookCreate) -> BookOrm:
        book = BookOrm(**payload.model_dump())
        self._session.add(book)
        await self._session.flush()
        return book

    async def update_book(self, book_id: uuid.UUID, payload: BookUpdate) -> BookOrm | None:
        book = await self.read_book_by_id(book_id)
        if book is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(book, field, value)
        await self._session.flush()
        return book

    async def soft_delete_book(self, book_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(BookOrm)
            .where(BookOrm.id == book_id, BookOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(BookOrm.id)
        )
        return deleted_id is not None

    async def read_book_by_id(self, book_id: uuid.UUID) -> BookOrm | None:
        return await self._session.scalar(
            select(BookOrm).where(BookOrm.id == book_id, BookOrm.deleted_at.is_(None))
        )

    async def read_books_by_ids(self, book_ids: list[uuid.UUID]) -> list[BookOrm]:
        if not book_ids:
            return []
        result = await self._session.scalars(
            select(BookOrm).where(BookOrm.id.in_(book_ids), BookOrm.deleted_at.is_(None))
        )
        return list(result)

    async def count_books(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(BookOrm).where(BookOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_books(self, *, offset: int, limit: int) -> list[BookOrm]:
        statement: Select[tuple[BookOrm]] = (
            select(BookOrm)
            .where(BookOrm.deleted_at.is_(None))
            .order_by(BookOrm.title)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)

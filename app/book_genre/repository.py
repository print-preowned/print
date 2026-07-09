from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.book_genre.orm import BookGenreOrm
from app.book_genre.schemas import BookGenreCreate, BookGenreUpdate


class BookGenreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_book_genre(self, payload: BookGenreCreate) -> BookGenreOrm:
        row = BookGenreOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_book_genre(
        self, mapping_id: uuid.UUID, payload: BookGenreUpdate
    ) -> BookGenreOrm | None:
        row = await self.read_book_genre_by_id(mapping_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def soft_delete_book_genre(self, mapping_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(BookGenreOrm)
            .where(BookGenreOrm.id == mapping_id, BookGenreOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(BookGenreOrm.id)
        )
        return deleted_id is not None

    async def soft_delete_by_book_and_genre(self, book_id: uuid.UUID, genre_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
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

    async def read_book_genre_by_id(self, mapping_id: uuid.UUID) -> BookGenreOrm | None:
        return await self._session.scalar(
            select(BookGenreOrm).where(
                BookGenreOrm.id == mapping_id, BookGenreOrm.deleted_at.is_(None)
            )
        )

    async def read_by_book_id(self, book_id: uuid.UUID) -> list[BookGenreOrm]:
        result = await self._session.scalars(
            select(BookGenreOrm).where(
                BookGenreOrm.book_id == book_id, BookGenreOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def read_by_book_ids(self, book_ids: list[uuid.UUID]) -> list[BookGenreOrm]:
        if not book_ids:
            return []
        result = await self._session.scalars(
            select(BookGenreOrm).where(
                BookGenreOrm.book_id.in_(book_ids), BookGenreOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def read_by_genre_id(self, genre_id: uuid.UUID) -> list[BookGenreOrm]:
        result = await self._session.scalars(
            select(BookGenreOrm).where(
                BookGenreOrm.genre_id == genre_id, BookGenreOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def count_book_genres(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(BookGenreOrm).where(BookGenreOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_book_genres(self, *, offset: int, limit: int) -> list[BookGenreOrm]:
        statement: Select[tuple[BookGenreOrm]] = (
            select(BookGenreOrm)
            .where(BookGenreOrm.deleted_at.is_(None))
            .order_by(BookGenreOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)

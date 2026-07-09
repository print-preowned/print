from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.book_author.orm import BookAuthorOrm
from app.book_author.schemas import BookAuthorCreate, BookAuthorUpdate


class BookAuthorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_book_author(self, payload: BookAuthorCreate) -> BookAuthorOrm:
        row = BookAuthorOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_book_author(
        self, mapping_id: uuid.UUID, payload: BookAuthorUpdate
    ) -> BookAuthorOrm | None:
        row = await self.read_book_author_by_id(mapping_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def soft_delete_book_author(self, mapping_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(BookAuthorOrm)
            .where(BookAuthorOrm.id == mapping_id, BookAuthorOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(BookAuthorOrm.id)
        )
        return deleted_id is not None

    async def soft_delete_by_book_and_author(
        self, book_id: uuid.UUID, author_id: uuid.UUID
    ) -> bool:
        deleted_id = await self._session.scalar(
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

    async def read_book_author_by_id(self, mapping_id: uuid.UUID) -> BookAuthorOrm | None:
        return await self._session.scalar(
            select(BookAuthorOrm).where(
                BookAuthorOrm.id == mapping_id, BookAuthorOrm.deleted_at.is_(None)
            )
        )

    async def read_by_book_id(self, book_id: uuid.UUID) -> list[BookAuthorOrm]:
        result = await self._session.scalars(
            select(BookAuthorOrm).where(
                BookAuthorOrm.book_id == book_id, BookAuthorOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def read_by_book_ids(self, book_ids: list[uuid.UUID]) -> list[BookAuthorOrm]:
        if not book_ids:
            return []
        result = await self._session.scalars(
            select(BookAuthorOrm).where(
                BookAuthorOrm.book_id.in_(book_ids), BookAuthorOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def read_by_author_id(self, author_id: uuid.UUID) -> list[BookAuthorOrm]:
        result = await self._session.scalars(
            select(BookAuthorOrm).where(
                BookAuthorOrm.author_id == author_id, BookAuthorOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def count_book_authors(self) -> int:
        from sqlalchemy import func

        total = await self._session.scalar(
            select(func.count())
            .select_from(BookAuthorOrm)
            .where(BookAuthorOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_book_authors(self, *, offset: int, limit: int) -> list[BookAuthorOrm]:
        from sqlalchemy import Select

        statement: Select[tuple[BookAuthorOrm]] = (
            select(BookAuthorOrm)
            .where(BookAuthorOrm.deleted_at.is_(None))
            .order_by(BookAuthorOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)

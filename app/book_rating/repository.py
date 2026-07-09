from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.book_rating.orm import BookRatingOrm
from app.book_rating.schemas import BookRatingCreate, BookRatingUpdate


class BookRatingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_book_rating(self, payload: BookRatingCreate) -> BookRatingOrm:
        row = BookRatingOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_book_rating(
        self, rating_id: uuid.UUID, payload: BookRatingUpdate
    ) -> BookRatingOrm | None:
        row = await self.read_book_rating_by_id(rating_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def soft_delete_book_rating(self, rating_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(BookRatingOrm)
            .where(BookRatingOrm.id == rating_id, BookRatingOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(BookRatingOrm.id)
        )
        return deleted_id is not None

    async def read_book_rating_by_id(self, rating_id: uuid.UUID) -> BookRatingOrm | None:
        return await self._session.scalar(
            select(BookRatingOrm).where(
                BookRatingOrm.id == rating_id, BookRatingOrm.deleted_at.is_(None)
            )
        )

    async def read_by_book_id(self, book_id: uuid.UUID) -> list[BookRatingOrm]:
        result = await self._session.scalars(
            select(BookRatingOrm).where(
                BookRatingOrm.book_id == book_id, BookRatingOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def read_by_user_id(self, user_id: uuid.UUID) -> list[BookRatingOrm]:
        result = await self._session.scalars(
            select(BookRatingOrm).where(
                BookRatingOrm.user_id == user_id, BookRatingOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def count_book_ratings(self) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(BookRatingOrm)
            .where(BookRatingOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_book_ratings(self, *, offset: int, limit: int) -> list[BookRatingOrm]:
        statement: Select[tuple[BookRatingOrm]] = (
            select(BookRatingOrm)
            .where(BookRatingOrm.deleted_at.is_(None))
            .order_by(BookRatingOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)

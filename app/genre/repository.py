from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import ColumnElement, Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.genre.orm import GenreOrm
from app.genre.schemas import GenreCreate, GenreUpdate


def not_deleted() -> ColumnElement[bool]:
    return GenreOrm.deleted_at.is_(None)


class GenreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_genre(self, payload: GenreCreate) -> GenreOrm:
        genre = GenreOrm(**payload.model_dump())
        self._session.add(genre)
        await self._session.flush()
        return genre

    async def update_genre(self, genre_id: uuid.UUID, payload: GenreUpdate) -> GenreOrm | None:
        genre = await self.read_genre_by_id(genre_id)
        if genre is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(genre, field, value)
        await self._session.flush()
        return genre

    async def soft_delete_genre(self, genre_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(GenreOrm)
            .where(GenreOrm.id == genre_id, GenreOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC))
            .returning(GenreOrm.id)
        )
        return deleted_id is not None

    async def read_genre_by_id(self, genre_id: uuid.UUID) -> GenreOrm | None:
        return await self._session.scalar(
            select(GenreOrm).where(GenreOrm.id == genre_id, GenreOrm.deleted_at.is_(None))
        )

    async def read_genres_by_ids(self, genre_ids: list[uuid.UUID]) -> list[GenreOrm]:
        if not genre_ids:
            return []
        result = await self._session.scalars(
            select(GenreOrm).where(GenreOrm.id.in_(genre_ids), GenreOrm.deleted_at.is_(None))
        )
        return list(result)

    async def count_genres(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(GenreOrm).where(GenreOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_genres(self, *, offset: int, limit: int) -> list[GenreOrm]:
        statement: Select[tuple[GenreOrm]] = (
            select(GenreOrm)
            .where(GenreOrm.deleted_at.is_(None))
            .order_by(GenreOrm.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)

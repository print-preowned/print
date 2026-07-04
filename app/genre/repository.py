from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import ColumnElement, Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.genre.orm import GenreOrm
from app.genre.schemas import GenreCreate, GenreUpdate


def not_deleted() -> ColumnElement[bool]:
    return GenreOrm.deleted_at.is_(None)


async def create_genre(session: AsyncSession, payload: GenreCreate) -> GenreOrm:
    genre = GenreOrm(**payload.model_dump())
    session.add(genre)
    await session.flush()
    return genre


async def update_genre(
    session: AsyncSession,
    genre_id: uuid.UUID,
    payload: GenreUpdate,
) -> GenreOrm | None:
    genre = await read_genre_by_id(session, genre_id)
    if genre is None:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(genre, field, value)
    await session.flush()
    return genre


async def soft_delete_genre(session: AsyncSession, genre_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(GenreOrm)
        .where(GenreOrm.id == genre_id, GenreOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC))
        .returning(GenreOrm.id)
    )
    return deleted_id is not None


async def read_genre_by_id(session: AsyncSession, genre_id: uuid.UUID) -> GenreOrm | None:
    return await session.scalar(
        select(GenreOrm).where(GenreOrm.id == genre_id, GenreOrm.deleted_at.is_(None))
    )


async def read_genres_by_ids(session: AsyncSession, genre_ids: list[uuid.UUID]) -> list[GenreOrm]:
    if not genre_ids:
        return []
    result = await session.scalars(
        select(GenreOrm).where(GenreOrm.id.in_(genre_ids), GenreOrm.deleted_at.is_(None))
    )
    return list(result)


async def count_genres(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(GenreOrm).where(GenreOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_genres(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[GenreOrm]:
    statement: Select[tuple[GenreOrm]] = (
        select(GenreOrm)
        .where(GenreOrm.deleted_at.is_(None))
        .order_by(GenreOrm.name)
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)


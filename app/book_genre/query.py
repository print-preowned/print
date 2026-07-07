from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.book_genre.model import BookGenreCreateRequest, BookGenreUpdateRequest
from app.book_genre.repository import (
    count_book_genres,
    create_book_genre,
    list_book_genres,
    read_book_genre_by_id,
    read_by_book_id,
    read_by_book_ids,
    read_by_genre_id,
    soft_delete_book_genre,
    soft_delete_by_book_and_genre,
    update_book_genre,
)
from app.book_genre.schemas import BookGenreCreate, BookGenreRead, BookGenreUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BookGenreRead:
    return BookGenreRead.model_validate(row)


async def create_query(mapping: BookGenreCreateRequest) -> None:
    payload = BookGenreCreate(
        book_id=_parse_id(mapping.book_id),
        genre_id=_parse_id(mapping.genre_id),
    )
    async with get_sessionmaker()() as session:
        await create_book_genre(session, payload)
        await session.commit()


async def update_query(id: str, mapping: BookGenreUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    update_data = mapping.model_dump(exclude_unset=True)
    if "book_id" in update_data and update_data["book_id"] is not None:
        update_data["book_id"] = _parse_id(update_data["book_id"])
    if "genre_id" in update_data and update_data["genre_id"] is not None:
        update_data["genre_id"] = _parse_id(update_data["genre_id"])

    async with get_sessionmaker()() as session:
        updated = await update_book_genre(
            session,
            parsed_id,
            BookGenreUpdate.model_validate(update_data),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_book_genre(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_by_book_and_genre_query(book_id: str, genre_id: str) -> UpdateResult:
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_by_book_and_genre(
            session,
            _parse_id(book_id),
            _parse_id(genre_id),
        )
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[BookGenreRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_book_genres(session)
        rows = await list_book_genres(session, offset=offset, limit=size)

    total_pages = math.ceil(total_results / size) if size else 1
    return PaginatedData(
        data=[_to_read(row) for row in rows],
        pagination=Pagination(
            page=page,
            size=size,
            total_pages=total_pages,
            total_results=total_results,
        ),
    )


async def read_by_id_query(id: str) -> BookGenreRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_book_genre_by_id(session, parsed_id)
    if row is None:
        return None
    return _to_read(row)


async def read_by_book_id_query(book_id: str) -> list[BookGenreRead]:
    async with get_sessionmaker()() as session:
        rows = await read_by_book_id(session, _parse_id(book_id))
    return [_to_read(row) for row in rows]


async def read_by_book_ids_query(book_ids: list[str]) -> list[BookGenreRead]:
    if not book_ids:
        return []
    parsed_ids = [_parse_id(book_id) for book_id in book_ids]
    async with get_sessionmaker()() as session:
        rows = await read_by_book_ids(session, parsed_ids)
    return [_to_read(row) for row in rows]


async def read_by_genre_id_query(genre_id: str) -> list[BookGenreRead]:
    async with get_sessionmaker()() as session:
        rows = await read_by_genre_id(session, _parse_id(genre_id))
    return [_to_read(row) for row in rows]

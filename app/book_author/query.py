from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.book_author.model import BookAuthorCreateRequest, BookAuthorUpdateRequest
from app.book_author.repository import BookAuthorRepository
from app.book_author.schemas import BookAuthorCreate, BookAuthorRead, BookAuthorUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BookAuthorRead:
    return BookAuthorRead.model_validate(row)


async def create_query(mapping: BookAuthorCreateRequest) -> None:
    payload = BookAuthorCreate(
        book_id=_parse_id(mapping.book_id),
        author_id=_parse_id(mapping.author_id),
    )
    async with get_sessionmaker()() as session:
        await BookAuthorRepository(session).create_book_author(payload)
        await session.commit()


async def update_query(id: str, mapping: BookAuthorUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    update_data = mapping.model_dump(exclude_unset=True)
    if "book_id" in update_data and update_data["book_id"] is not None:
        update_data["book_id"] = _parse_id(update_data["book_id"])
    if "author_id" in update_data and update_data["author_id"] is not None:
        update_data["author_id"] = _parse_id(update_data["author_id"])

    async with get_sessionmaker()() as session:
        updated = await BookAuthorRepository(session).update_book_author(
            parsed_id,
            BookAuthorUpdate.model_validate(update_data),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await BookAuthorRepository(session).soft_delete_book_author(parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_by_book_and_author_query(book_id: str, author_id: str) -> UpdateResult:
    async with get_sessionmaker()() as session:
        deleted = await BookAuthorRepository(session).soft_delete_by_book_and_author(
            _parse_id(book_id),
            _parse_id(author_id),
        )
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[BookAuthorRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await BookAuthorRepository(session).count_book_authors()
        rows = await BookAuthorRepository(session).list_book_authors(offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> BookAuthorRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await BookAuthorRepository(session).read_book_author_by_id(parsed_id)
    if row is None:
        return None
    return _to_read(row)


async def read_by_book_id_query(book_id: str) -> list[BookAuthorRead]:
    async with get_sessionmaker()() as session:
        rows = await BookRatingRepository(session).read_by_book_id(_parse_id(book_id))
    return [_to_read(row) for row in rows]


async def read_by_book_ids_query(book_ids: list[str]) -> list[BookAuthorRead]:
    if not book_ids:
        return []
    parsed_ids = [_parse_id(book_id) for book_id in book_ids]
    async with get_sessionmaker()() as session:
        rows = await BookGenreRepository(session).read_by_book_ids(parsed_ids)
    return [_to_read(row) for row in rows]


async def read_by_author_id_query(author_id: str) -> list[BookAuthorRead]:
    async with get_sessionmaker()() as session:
        rows = await BookAuthorRepository(session).read_by_author_id(_parse_id(author_id))
    return [_to_read(row) for row in rows]

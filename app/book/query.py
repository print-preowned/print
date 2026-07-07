from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.book.model import BookCreateRequest, BookUpdateRequest
from app.book.repository import (
    create_book,
    list_books,
    read_book_by_id,
    soft_delete_book,
    update_book,
    count_books,
)
from app.book.schemas import BookCreate, BookRead, BookUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BookRead:
    return BookRead.model_validate(row)


async def create_query(book: BookCreateRequest) -> str:
    payload = BookCreate.model_validate(
        book.model_dump(include=set(BookCreate.model_fields.keys()))
    )
    async with get_sessionmaker()() as session:
        created = await create_book(session, payload)
        await session.commit()
        return str(created.id)


async def update_query(id: str, book: BookUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_book(
            session,
            parsed_id,
            BookUpdate.model_validate(book.model_dump(exclude_unset=True, exclude={"author_ids", "genre_ids"})),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_book(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[BookRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_books(session)
        rows = await list_books(session, offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> BookRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_book_by_id(session, parsed_id)
    return _to_read(row) if row else None

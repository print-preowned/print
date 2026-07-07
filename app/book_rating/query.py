from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.book_rating.model import BookRatingCreateRequest, BookRatingUpdateRequest
from app.book_rating.repository import (
    count_book_ratings,
    create_book_rating,
    list_book_ratings,
    read_book_rating_by_id,
    read_by_book_id,
    read_by_user_id,
    soft_delete_book_rating,
    update_book_rating,
)
from app.book_rating.schemas import BookRatingCreate, BookRatingRead, BookRatingUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BookRatingRead:
    return BookRatingRead.model_validate(row)


def _to_create(payload: BookRatingCreateRequest) -> BookRatingCreate:
    data = payload.model_dump(include=set(BookRatingCreate.model_fields.keys()))
    data["book_id"] = _parse_id(str(data["book_id"]))
    data["user_id"] = _parse_id(str(data["user_id"]))
    return BookRatingCreate.model_validate(data)


async def create_query(rating: BookRatingCreateRequest) -> None:
    async with get_sessionmaker()() as session:
        await create_book_rating(session, _to_create(rating))
        await session.commit()


async def update_query(id: str, rating: BookRatingUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    update_data = rating.model_dump(exclude_unset=True)
    if "book_id" in update_data and update_data["book_id"] is not None:
        update_data["book_id"] = _parse_id(str(update_data["book_id"]))
    if "user_id" in update_data and update_data["user_id"] is not None:
        update_data["user_id"] = _parse_id(str(update_data["user_id"]))

    async with get_sessionmaker()() as session:
        updated = await update_book_rating(
            session,
            parsed_id,
            BookRatingUpdate.model_validate(update_data),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_book_rating(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[BookRatingRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_book_ratings(session)
        rows = await list_book_ratings(session, offset=offset, limit=size)
        data = [_to_read(row) for row in rows]

    total_pages = math.ceil(total_results / size) if size else 1
    return PaginatedData(
        data=data,
        pagination=Pagination(
            page=page,
            size=size,
            total_pages=total_pages,
            total_results=total_results,
        ),
    )


async def read_by_id_query(id: str) -> BookRatingRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_book_rating_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_book_id_query(book_id: str) -> list[BookRatingRead]:
    async with get_sessionmaker()() as session:
        rows = await read_by_book_id(session, _parse_id(book_id))
    return [_to_read(row) for row in rows]


async def read_by_user_id_query(user_id: str) -> list[BookRatingRead]:
    async with get_sessionmaker()() as session:
        rows = await read_by_user_id(session, _parse_id(user_id))
    return [_to_read(row) for row in rows]

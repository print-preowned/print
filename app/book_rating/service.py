from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.book_rating.model import BookRatingCreateRequest, BookRatingUpdateRequest
from app.book_rating.repository import BookRatingRepository
from app.book_rating.schemas import BookRatingCreate, BookRatingRead, BookRatingUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BookRatingRead:
    return BookRatingRead.model_validate(row)


def _to_create(payload: BookRatingCreateRequest) -> BookRatingCreate:
    data = payload.model_dump(include=set(BookRatingCreate.model_fields.keys()))
    data["book_id"] = _parse_id(str(data["book_id"]))
    data["user_id"] = _parse_id(str(data["user_id"]))
    return BookRatingCreate.model_validate(data)


class BookRatingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BookRatingRepository(session)

    async def create(self, rating: BookRatingCreateRequest) -> Response:
        await self._repo.create_book_rating(_to_create(rating))
        return Response(status_code=201)

    async def update(self, id: str, rating: BookRatingUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        update_data = rating.model_dump(exclude_unset=True)
        if "book_id" in update_data and update_data["book_id"] is not None:
            update_data["book_id"] = _parse_id(str(update_data["book_id"]))
        if "user_id" in update_data and update_data["user_id"] is not None:
            update_data["user_id"] = _parse_id(str(update_data["user_id"]))

        updated = await self._repo.update_book_rating(
            parsed_id,
            BookRatingUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Rating not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await self._repo.soft_delete_book_rating(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Rating not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[BookRatingRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_book_ratings()
        rows = await self._repo.list_book_ratings(offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[BookRatingRead](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id(self, id: str) -> BaseResponse[BookRatingRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_book_rating_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Rating not found")
        return BaseResponse[BookRatingRead](
            status_code=200, message="Successful", data=_to_read(row)
        )

    async def read_by_book_id(self, book_id: str) -> BaseResponse[list[BookRatingRead]]:
        rows = await self._repo.read_by_book_id(_parse_id(book_id))
        return BaseResponse[list[BookRatingRead]](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
        )

    async def read_by_user_id(self, user_id: str) -> BaseResponse[list[BookRatingRead]]:
        rows = await self._repo.read_by_user_id(_parse_id(user_id))
        return BaseResponse[list[BookRatingRead]](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
        )


class WritableBookRatingService(writable_service(BookRatingService)):
    pass


class ReadableBookRatingService(readable_service(BookRatingService)):
    pass

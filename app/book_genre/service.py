from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.book_genre.model import BookGenreCreateRequest, BookGenreUpdateRequest
from app.book_genre.repository import (
    count_book_genres,
    create_book_genre,
    list_book_genres,
    read_book_genre_by_id,
    read_by_book_id,
    read_by_genre_id,
    soft_delete_book_genre,
    soft_delete_by_book_and_genre,
    update_book_genre,
)
from app.book_genre.schemas import BookGenreCreate, BookGenreRead, BookGenreUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BookGenreRead:
    return BookGenreRead.model_validate(row)


class BookGenreService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, mapping: BookGenreCreateRequest) -> Response:
        payload = BookGenreCreate(
            book_id=_parse_id(mapping.book_id),
            genre_id=_parse_id(mapping.genre_id),
        )
        await create_book_genre(self._session, payload)
        return Response(status_code=201)

    async def update(self, id: str, mapping: BookGenreUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        update_data = mapping.model_dump(exclude_unset=True)
        if "book_id" in update_data and update_data["book_id"] is not None:
            update_data["book_id"] = _parse_id(update_data["book_id"])
        if "genre_id" in update_data and update_data["genre_id"] is not None:
            update_data["genre_id"] = _parse_id(update_data["genre_id"])

        updated = await update_book_genre(
            self._session,
            parsed_id,
            BookGenreUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await soft_delete_book_genre(self._session, parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return Response(status_code=204)

    async def delete_by_book_and_genre(self, book_id: str, genre_id: str) -> Response:
        deleted = await soft_delete_by_book_and_genre(
            self._session,
            _parse_id(book_id),
            _parse_id(genre_id),
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[BookGenreRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await count_book_genres(self._session)
        rows = await list_book_genres(self._session, offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[BookGenreRead](
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

    async def read_by_id(self, id: str) -> BaseResponse[BookGenreRead]:
        parsed_id = _parse_id(id)
        row = await read_book_genre_by_id(self._session, parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return BaseResponse[BookGenreRead](status_code=200, message="Successful", data=_to_read(row))

    async def read_by_book_id(self, book_id: str) -> BaseResponse[list[BookGenreRead]]:
        rows = await read_by_book_id(self._session, _parse_id(book_id))
        return BaseResponse[list[BookGenreRead]](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
        )

    async def read_by_genre_id(self, genre_id: str) -> BaseResponse[list[BookGenreRead]]:
        rows = await read_by_genre_id(self._session, _parse_id(genre_id))
        return BaseResponse[list[BookGenreRead]](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
        )


from app.utility.service_deps import readable_service, writable_service

WritableBookGenreService = writable_service(BookGenreService)
ReadableBookGenreService = readable_service(BookGenreService)

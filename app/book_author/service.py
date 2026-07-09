from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.book_author.model import BookAuthorCreateRequest, BookAuthorUpdateRequest
from app.book_author.repository import BookAuthorRepository
from app.book_author.schemas import BookAuthorCreate, BookAuthorRead, BookAuthorUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BookAuthorRead:
    return BookAuthorRead.model_validate(row)


class BookAuthorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BookAuthorRepository(session)

    async def create(self, mapping: BookAuthorCreateRequest) -> Response:
        payload = BookAuthorCreate(
            book_id=_parse_id(mapping.book_id),
            author_id=_parse_id(mapping.author_id),
        )
        await self._repo.create_book_author(payload)
        return Response(status_code=201)

    async def update(self, id: str, mapping: BookAuthorUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        update_data = mapping.model_dump(exclude_unset=True)
        if "book_id" in update_data and update_data["book_id"] is not None:
            update_data["book_id"] = _parse_id(update_data["book_id"])
        if "author_id" in update_data and update_data["author_id"] is not None:
            update_data["author_id"] = _parse_id(update_data["author_id"])

        updated = await self._repo.update_book_author(
            parsed_id,
            BookAuthorUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await self._repo.soft_delete_book_author(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return Response(status_code=204)

    async def delete_by_book_and_author(self, book_id: str, author_id: str) -> Response:
        deleted = await self._repo.soft_delete_by_book_and_author(
            _parse_id(book_id),
            _parse_id(author_id),
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[BookAuthorRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_book_authors()
        rows = await self._repo.list_book_authors(offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[BookAuthorRead](
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

    async def read_by_id(self, id: str) -> BaseResponse[BookAuthorRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_book_author_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return BaseResponse[BookAuthorRead](
            status_code=200, message="Successful", data=_to_read(row)
        )

    async def read_by_book_id(self, book_id: str) -> BaseResponse[list[BookAuthorRead]]:
        rows = await self._repo.read_by_book_id(_parse_id(book_id))
        return BaseResponse[list[BookAuthorRead]](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
        )

    async def read_by_author_id(self, author_id: str) -> BaseResponse[list[BookAuthorRead]]:
        rows = await self._repo.read_by_author_id(_parse_id(author_id))
        return BaseResponse[list[BookAuthorRead]](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
        )


WritableBookAuthorService = writable_service(BookAuthorService)
ReadableBookAuthorService = readable_service(BookAuthorService)

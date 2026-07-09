from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.author.model import AuthorCreateRequest, AuthorUpdateRequest
from app.author.repository import AuthorRepository
from app.author.schemas import AuthorCreate, AuthorRead, AuthorUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> AuthorRead:
    return AuthorRead.model_validate(row)


def _to_create(payload: AuthorCreateRequest) -> AuthorCreate:
    return AuthorCreate.model_validate(
        payload.model_dump(include=set(AuthorCreate.model_fields.keys()))
    )


class AuthorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AuthorRepository(session)

    async def create(self, author: AuthorCreateRequest) -> Response:
        created = await self._repo.create_author(_to_create(author))
        return JSONResponse(
            status_code=201,
            content={"id": str(created.id), "message": "Author created"},
        )

    async def update(self, id: str, author: AuthorUpdateRequest) -> Response:
        updated = await self._repo.update_author(
            _parse_id(id),
            AuthorUpdate.model_validate(author.model_dump(exclude_unset=True)),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Author not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        deleted = await self._repo.soft_delete_author(_parse_id(id))
        if not deleted:
            raise HTTPException(status_code=404, detail="Author not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[AuthorRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_authors()
        rows = await self._repo.list_authors(offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[AuthorRead](
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

    async def read_by_id(self, id: str) -> BaseResponse[AuthorRead]:
        row = await self._repo.read_author_by_id(_parse_id(id))
        if row is None:
            raise HTTPException(status_code=404, detail="Author not found")
        return BaseResponse[AuthorRead](
            status_code=200,
            message="Successful",
            data=_to_read(row),
        )

    async def merge(self, source_author_id: str, target_author_id: str) -> Response:
        raise HTTPException(status_code=501, detail="Not implemented yet")

    async def promote(self, id: str) -> Response:
        raise HTTPException(status_code=501, detail="Not implemented yet")

    async def deprecate(self, id: str) -> Response:
        raise HTTPException(status_code=501, detail="Not implemented yet")


class WritableAuthorService(writable_service(AuthorService)):
    pass


class ReadableAuthorService(readable_service(AuthorService)):
    pass

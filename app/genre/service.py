from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.genre.orm import GenreOrm
from app.genre.repository import GenreRepository
from app.genre.schemas import GenreCreate, GenreRead, GenreUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _parse_genre_id(genre_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(genre_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Genre not found") from exc


def _to_read(row: GenreOrm) -> GenreRead:
    return GenreRead.model_validate(row)


class GenreService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = GenreRepository(session)

    async def create(self, payload: GenreCreate) -> Response:
        try:
            await self._repo.create_genre(payload)
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Genre name already exists") from exc
        return Response(status_code=201)

    async def update(self, genre_id: str, payload: GenreUpdate) -> Response:
        parsed_id = _parse_genre_id(genre_id)
        updated = await self._repo.update_genre(parsed_id, payload)
        if updated is None:
            raise HTTPException(status_code=404, detail="Genre not found")
        return Response(status_code=200)

    async def delete(self, genre_id: str) -> Response:
        parsed_id = _parse_genre_id(genre_id)
        deleted = await self._repo.soft_delete_genre(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Genre not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[GenreRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_genres()
        rows = await self._repo.list_genres(offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[GenreRead](
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

    async def read_by_id(self, genre_id: str) -> BaseResponse[GenreRead]:
        parsed_id = _parse_genre_id(genre_id)
        row = await self._repo.read_genre_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Genre not found")
        return BaseResponse[GenreRead](status_code=200, message="Successful", data=_to_read(row))


WritableGenreService = writable_service(GenreService)
ReadableGenreService = readable_service(GenreService)

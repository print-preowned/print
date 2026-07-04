from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.exc import IntegrityError

from app.genre.orm import GenreOrm
from app.genre.schemas import GenreCreate, GenreRead, GenreUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker

from . import repository


def _parse_genre_id(genre_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(genre_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Genre not found") from exc


def _to_read(row: GenreOrm) -> GenreRead:
    return GenreRead.model_validate(row)


async def create_service(payload: GenreCreate) -> Response:
    async with get_sessionmaker()() as session:
        try:
            await repository.create_genre(session, payload)
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(status_code=409, detail="Genre name already exists") from exc
    return Response(status_code=201)


async def update_service(genre_id: str, payload: GenreUpdate) -> Response:
    parsed_id = _parse_genre_id(genre_id)
    async with get_sessionmaker()() as session:
        updated = await repository.update_genre(session, parsed_id, payload)
        if updated is None:
            raise HTTPException(status_code=404, detail="Genre not found")
        await session.commit()
    return Response(status_code=200)


async def delete_service(genre_id: str) -> Response:
    parsed_id = _parse_genre_id(genre_id)
    async with get_sessionmaker()() as session:
        deleted = await repository.soft_delete_genre(session, parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Genre not found")
        await session.commit()
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[GenreRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await repository.count_genres(session)
        rows = await repository.list_genres(session, offset=offset, limit=size)

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


async def read_by_id_service(genre_id: str) -> BaseResponse[GenreRead]:
    parsed_id = _parse_genre_id(genre_id)
    async with get_sessionmaker()() as session:
        row = await repository.read_genre_by_id(session, parsed_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Genre not found")
    return BaseResponse[GenreRead](status_code=200, message="Successful", data=_to_read(row))

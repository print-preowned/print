from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.author.model import AuthorCreateRequest, AuthorUpdateRequest
from app.author.repository import AuthorRepository
from app.author.schemas import AuthorCreate, AuthorRead, AuthorUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> AuthorRead:
    return AuthorRead.model_validate(row)


def _to_create(payload: AuthorCreateRequest) -> AuthorCreate:
    return AuthorCreate.model_validate(
        payload.model_dump(include=set(AuthorCreate.model_fields.keys()))
    )


async def create_query(author: AuthorCreateRequest) -> str:
    async with get_sessionmaker()() as session:
        created = await AuthorRepository(session).create_author(_to_create(author))
        await session.commit()
        return str(created.id)


async def update_query(id: str, author: AuthorUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await AuthorRepository(session).update_author(
            parsed_id,
            AuthorUpdate.model_validate(author.model_dump(exclude_unset=True)),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await AuthorRepository(session).soft_delete_author(parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[AuthorRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await AuthorRepository(session).count_authors()
        rows = await AuthorRepository(session).list_authors(offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> AuthorRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await AuthorRepository(session).read_author_by_id(parsed_id)
    if row is None:
        return None
    return _to_read(row)


async def read_by_ids_query(ids: list[str]) -> list[AuthorRead]:
    if not ids:
        return []
    parsed_ids = [_parse_id(value) for value in ids]
    async with get_sessionmaker()() as session:
        rows = await AuthorRepository(session).read_authors_by_ids(parsed_ids)
    return [_to_read(row) for row in rows]

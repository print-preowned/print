from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.business.model import BusinessCreateRequest, BusinessUpdateRequest
from app.business.repository import BusinessRepository
from app.business.schemas import BusinessCreate, BusinessRead, BusinessUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_business_id(business_id: str) -> uuid.UUID:
    return uuid.UUID(business_id)


def _to_business_update(payload: BusinessUpdateRequest) -> BusinessUpdate:
    data = payload.model_dump(exclude_unset=True)
    user_id = data.pop("user_id", None)
    if user_id is not None:
        data["user_id"] = uuid.UUID(str(user_id))
    return BusinessUpdate(**data)


def _to_read(row) -> BusinessRead:
    return BusinessRead.model_validate(row)


async def create_query(business: BusinessCreateRequest) -> None:
    if business.user_id is None:
        raise ValueError("user_id is required")
    payload = BusinessCreate.model_validate(
        business.model_dump() | {"user_id": uuid.UUID(str(business.user_id))}
    )
    async with get_sessionmaker()() as session:
        await BusinessRepository(session).create(payload)
        await session.commit()


async def update_query(id: str, business: BusinessUpdateRequest) -> UpdateResult:
    parsed_id = _parse_business_id(id)
    async with get_sessionmaker()() as session:
        updated = await BusinessRepository(session).update(parsed_id, _to_business_update(business))
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
        return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_business_id(id)
    async with get_sessionmaker()() as session:
        deleted = await BusinessRepository(session).delete(parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
        return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[BusinessRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await BusinessRepository(session).count()
        rows = await BusinessRepository(session).list(offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> BusinessRead | None:
    async with get_sessionmaker()() as session:
        row = await BusinessRepository(session).read_by_id(_parse_business_id(id))
    return _to_read(row) if row else None


async def read_by_user_id_query(user_id: str) -> BusinessRead | None:
    async with get_sessionmaker()() as session:
        row = await BusinessRepository(session).read_by_user_id(uuid.UUID(user_id))
    return _to_read(row) if row else None

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.business_rating.model import BusinessRatingCreateRequest, BusinessRatingUpdateRequest
from app.business_rating.repository import (
    count_business_ratings,
    create_business_rating,
    list_business_ratings,
    read_business_rating_by_id,
    read_by_business_id,
    soft_delete_business_rating,
    update_business_rating,
)
from app.business_rating.schemas import BusinessRatingCreate, BusinessRatingRead, BusinessRatingUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BusinessRatingRead:
    return BusinessRatingRead.model_validate(row)


def _to_create(payload: BusinessRatingCreateRequest) -> BusinessRatingCreate:
    data = payload.model_dump(include=set(BusinessRatingCreate.model_fields.keys()))
    data["business_id"] = _parse_id(str(data["business_id"]))
    data["user_id"] = _parse_id(str(data["user_id"]))
    if data.get("order_item_id") is not None:
        data["order_item_id"] = _parse_id(str(data["order_item_id"]))
    return BusinessRatingCreate.model_validate(data)


async def create_query(rating: BusinessRatingCreateRequest) -> None:
    async with get_sessionmaker()() as session:
        await create_business_rating(session, _to_create(rating))
        await session.commit()


async def update_query(id: str, rating: BusinessRatingUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    update_data = rating.model_dump(exclude_unset=True)
    if "business_id" in update_data and update_data["business_id"] is not None:
        update_data["business_id"] = _parse_id(str(update_data["business_id"]))
    if "user_id" in update_data and update_data["user_id"] is not None:
        update_data["user_id"] = _parse_id(str(update_data["user_id"]))
    if "order_item_id" in update_data and update_data["order_item_id"] is not None:
        update_data["order_item_id"] = _parse_id(str(update_data["order_item_id"]))

    async with get_sessionmaker()() as session:
        updated = await update_business_rating(
            session,
            parsed_id,
            BusinessRatingUpdate.model_validate(update_data),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_business_rating(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[BusinessRatingRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_business_ratings(session)
        rows = await list_business_ratings(session, offset=offset, limit=size)
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


async def read_by_id_query(id: str) -> BusinessRatingRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_business_rating_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_business_id_query(business_id: str) -> list[BusinessRatingRead]:
    async with get_sessionmaker()() as session:
        rows = await read_by_business_id(session, _parse_id(business_id))
    return [_to_read(row) for row in rows]

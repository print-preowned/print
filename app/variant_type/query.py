from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.variant_type.model import VariantTypeCreateRequest, VariantTypeUpdateRequest
from app.variant_type.repository import (
    create_product_option,
    list_product_options,
    read_product_option_by_id,
    soft_delete_product_option,
    update_product_option,
    count_product_options,
)
from app.variant_type.schemas import ProductOptionCreate, ProductOptionRead, ProductOptionUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> ProductOptionRead:
    return ProductOptionRead.model_validate(row)


async def create_query(item: VariantTypeCreateRequest) -> None:
    payload = ProductOptionCreate.model_validate(item.model_dump())
    async with get_sessionmaker()() as session:
        await create_product_option(session, payload)
        await session.commit()


async def update_query(id: str, item: VariantTypeUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_product_option(
            session,
            parsed_id,
            ProductOptionUpdate.model_validate(item.model_dump(exclude_unset=True)),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_product_option(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[ProductOptionRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_product_options(session)
        rows = await list_product_options(session, offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> ProductOptionRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_product_option_by_id(session, parsed_id)
    return _to_read(row) if row else None

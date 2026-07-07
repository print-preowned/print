from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.variant_option.model import VariantOptionCreateRequest, VariantOptionUpdateRequest
from app.variant_option.repository import (
    create_product_option_value,
    list_product_option_values,
    read_product_option_value_by_id,
    soft_delete_product_option_value,
    update_product_option_value,
    count_product_option_values,
)
from app.variant_option.schemas import (
    ProductOptionValueCreate,
    ProductOptionValueRead,
    ProductOptionValueUpdate,
)
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> ProductOptionValueRead:
    return ProductOptionValueRead.model_validate(row)


def _to_create(payload: VariantOptionCreateRequest) -> ProductOptionValueCreate:
    return ProductOptionValueCreate(
        product_option_id=uuid.UUID(str(payload.variant_type_id)),
        value=payload.value,
    )


def _to_update(payload: VariantOptionUpdateRequest) -> ProductOptionValueUpdate:
    data = payload.model_dump(exclude_unset=True)
    if "variant_type_id" in data and data["variant_type_id"] is not None:
        data["product_option_id"] = uuid.UUID(str(data.pop("variant_type_id")))
    return ProductOptionValueUpdate(**data)


async def create_query(item: VariantOptionCreateRequest) -> None:
    async with get_sessionmaker()() as session:
        await create_product_option_value(session, _to_create(item))
        await session.commit()


async def update_query(id: str, item: VariantOptionUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_product_option_value(session, parsed_id, _to_update(item))
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_product_option_value(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[ProductOptionValueRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_product_option_values(session)
        rows = await list_product_option_values(session, offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> ProductOptionValueRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_product_option_value_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_variant_type_query(
    variant_type_id: str,
    params: ParamRequest,
) -> PaginatedData[ProductOptionValueRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size
    parsed_option_id = _parse_id(variant_type_id)

    async with get_sessionmaker()() as session:
        total_results = await count_product_option_values(
            session,
            product_option_id=parsed_option_id,
        )
        rows = await list_product_option_values(
            session,
            offset=offset,
            limit=size,
            product_option_id=parsed_option_id,
        )

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

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.variant_config.model import VariantConfigCreateRequest, VariantConfigUpdateRequest
from app.variant_config.repository import (
    create_variant_product_option_value,
    list_variant_product_option_values,
    read_variant_product_option_value_by_id,
    soft_delete_variant_product_option_value,
    update_variant_product_option_value,
    count_variant_product_option_values,
)
from app.variant_config.schemas import (
    VariantProductOptionValueCreate,
    VariantProductOptionValueRead,
    VariantProductOptionValueUpdate,
)
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> VariantProductOptionValueRead:
    return VariantProductOptionValueRead.model_validate(row)


async def create_query(item: VariantConfigCreateRequest) -> None:
    payload = VariantProductOptionValueCreate(
        variant_id=uuid.UUID(str(item.variant_id)),
        product_option_value_id=uuid.UUID(str(item.variant_option_id)),
    )
    async with get_sessionmaker()() as session:
        await create_variant_product_option_value(session, payload)
        await session.commit()


async def update_query(id: str, item: VariantConfigUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_variant_product_option_value(
            session,
            parsed_id,
            VariantProductOptionValueUpdate.model_validate(item.model_dump(exclude_unset=True)),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_variant_product_option_value(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[VariantProductOptionValueRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_variant_product_option_values(session)
        rows = await list_variant_product_option_values(session, offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> VariantProductOptionValueRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_variant_product_option_value_by_id(session, parsed_id)
    return _to_read(row) if row else None

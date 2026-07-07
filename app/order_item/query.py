from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.order_item.model import OrderItemCreateRequest, OrderItemUpdateRequest
from app.order_item.repository import (
    count_order_items,
    create_order_item,
    list_order_items,
    read_order_item_by_id,
    soft_delete_order_item,
    update_order_item,
)
from app.order_item.schemas import OrderItemCreate, OrderItemRead, OrderItemUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> OrderItemRead:
    return OrderItemRead.model_validate(row)


def _to_create(payload: OrderItemCreateRequest) -> OrderItemCreate:
    data = payload.model_dump(include=set(OrderItemCreate.model_fields.keys()))
    data["order_id"] = _parse_id(str(data["order_id"]))
    data["variant_id"] = _parse_id(str(data["variant_id"]))
    data["unit_price"] = Decimal(str(data["unit_price"]))
    if data.get("discount_applied") is not None:
        data["discount_applied"] = Decimal(str(data["discount_applied"]))
    return OrderItemCreate.model_validate(data)


async def create_query(item: OrderItemCreateRequest) -> None:
    async with get_sessionmaker()() as session:
        await create_order_item(session, _to_create(item))
        await session.commit()


async def update_query(id: str, item: OrderItemUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    update_data = item.model_dump(exclude_unset=True)
    if "order_id" in update_data and update_data["order_id"] is not None:
        update_data["order_id"] = _parse_id(str(update_data["order_id"]))
    if "variant_id" in update_data and update_data["variant_id"] is not None:
        update_data["variant_id"] = _parse_id(str(update_data["variant_id"]))
    if "unit_price" in update_data and update_data["unit_price"] is not None:
        update_data["unit_price"] = Decimal(str(update_data["unit_price"]))
    if "discount_applied" in update_data and update_data["discount_applied"] is not None:
        update_data["discount_applied"] = Decimal(str(update_data["discount_applied"]))

    async with get_sessionmaker()() as session:
        updated = await update_order_item(
            session,
            parsed_id,
            OrderItemUpdate.model_validate(update_data),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_order_item(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[OrderItemRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_order_items(session)
        rows = await list_order_items(session, offset=offset, limit=size)
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


async def read_by_id_query(id: str) -> OrderItemRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_order_item_by_id(session, parsed_id)
    return _to_read(row) if row else None

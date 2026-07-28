from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.order_item.model import OrderItemCreateRequest, OrderItemUpdateRequest
from app.order_item.repository import OrderItemRepository
from app.order_item.schemas import OrderItemCreate, OrderItemRead, OrderItemUpdate
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, paginated_response
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> OrderItemRead:
    return OrderItemRead.model_validate(row)


def build_order_item_create(
    order_id: uuid.UUID,
    payload: OrderItemCreateRequest,
    currency: str,
) -> OrderItemCreate:
    discount = payload.discount_applied
    return OrderItemCreate(
        order_id=order_id,
        variant_id=_parse_id(payload.variant_id),
        quantity=payload.quantity,
        unit_price=Decimal(str(payload.unit_price)),
        currency=currency,
        discount_applied=Decimal(str(discount)) if discount is not None else None,
    )


def _assert_belongs_to_order(row, order_id: str) -> None:
    if str(row.order_id) != order_id:
        raise HTTPException(status_code=404, detail="OrderItem not found")


class OrderItemService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = OrderItemRepository(session)

    async def update(self, order_id: str, id: str, item: OrderItemUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        row = await self._repo.read_order_item_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="OrderItem not found")
        _assert_belongs_to_order(row, order_id)

        update_data = item.model_dump(exclude_unset=True)
        if "variant_id" in update_data and update_data["variant_id"] is not None:
            update_data["variant_id"] = _parse_id(str(update_data["variant_id"]))
        if "unit_price" in update_data and update_data["unit_price"] is not None:
            update_data["unit_price"] = Decimal(str(update_data["unit_price"]))
        if "discount_applied" in update_data and update_data["discount_applied"] is not None:
            update_data["discount_applied"] = Decimal(str(update_data["discount_applied"]))

        updated = await self._repo.update_order_item(
            parsed_id,
            OrderItemUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="OrderItem not found")
        return Response(status_code=200)

    async def delete(self, order_id: str, id: str) -> Response:
        parsed_id = _parse_id(id)
        row = await self._repo.read_order_item_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="OrderItem not found")
        _assert_belongs_to_order(row, order_id)

        deleted = await self._repo.delete_order_item(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="OrderItem not found")
        return Response(status_code=204)

    async def read(self, params: PaginationParams) -> PaginatedResponse[OrderItemRead]:
        total_results = await self._repo.count_order_items()
        rows = await self._repo.list_order_items(offset=params.offset, limit=params.size)
        return paginated_response([_to_read(row) for row in rows], total_results, params)

    async def read_by_id(self, order_id: str, id: str) -> BaseResponse[OrderItemRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_order_item_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="OrderItem not found")
        _assert_belongs_to_order(row, order_id)
        return BaseResponse[OrderItemRead](
            status_code=200, message="Successful", data=_to_read(row)
        )


class WritableOrderItemService(writable_service(OrderItemService)):
    pass


class ReadableOrderItemService(readable_service(OrderItemService)):
    pass

from __future__ import annotations

import math
import uuid
from decimal import Decimal

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.order.model import OrderCreateRequest, OrderUpdateRequest
from app.order_item.model import OrderItemCreateRequest
from app.order.repository import OrderRepository
from app.order.schemas import OrderCreate, OrderDetailRead, OrderRead, OrderUpdate
from app.order_item.repository import OrderItemRepository
from app.order_item.schemas import OrderItemRead
from app.order_item.service import build_order_item_create
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> OrderRead:
    return OrderRead.model_validate(row)


def _to_create(payload: OrderCreateRequest, user_id: str) -> OrderCreate:
    return OrderCreate(
        user_id=_parse_id(user_id),
        reference=payload.reference,
        total_amount=Decimal(str(payload.total_amount)),
    )


def _to_item_read(row) -> OrderItemRead:
    return OrderItemRead.model_validate(row)


def _to_detail_read(row, items: list[OrderItemRead]) -> OrderDetailRead:
    return OrderDetailRead(**_to_read(row).model_dump(), items=items)


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = OrderRepository(session)
        self._item_repo = OrderItemRepository(session)

    async def _read_items(self, order_id: uuid.UUID) -> list[OrderItemRead]:
        rows = await self._item_repo.list_order_items_by_order_id(order_id)
        return [_to_item_read(row) for row in rows]

    async def _get_owned_order(self, order_id: uuid.UUID, user_id: str):
        row = await self._repo.read_order_by_id(order_id)
        if row is None or str(row.user_id) != user_id:
            raise HTTPException(status_code=404, detail="Order not found")
        return row

    async def _create_items(self, order_id: uuid.UUID, currency: str, lines) -> list:
        item_rows = []
        for line in lines:
            item_rows.append(
                await self._item_repo.create_order_item(
                    build_order_item_create(order_id, line, currency)
                )
            )
        return item_rows

    async def create(
        self, order: OrderCreateRequest, user_id: str
    ) -> BaseResponse[OrderDetailRead]:
        create_payload = _to_create(order, user_id)
        row = await self._repo.create_order(create_payload)
        item_rows = await self._create_items(row.id, create_payload.currency, order.items)
        items = [_to_item_read(item_row) for item_row in item_rows]
        return BaseResponse[OrderDetailRead](
            status_code=201,
            message="Successful",
            data=_to_detail_read(row, items),
        )

    async def update(self, id: str, order: OrderUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        update_data = order.model_dump(exclude_unset=True)
        if "user_id" in update_data and update_data["user_id"] is not None:
            update_data["user_id"] = _parse_id(str(update_data["user_id"]))
        if "total_amount" in update_data and update_data["total_amount"] is not None:
            update_data["total_amount"] = Decimal(str(update_data["total_amount"]))

        updated = await self._repo.update_order(
            parsed_id,
            OrderUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await self._repo.soft_delete_order(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Order not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[OrderRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_orders()
        rows = await self._repo.list_orders(offset=offset, limit=size)
        data = [_to_read(row) for row in rows]

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[OrderRead](
            status_code=200,
            message="Successful",
            data=data,
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id(self, id: str, user_id: str | None = None) -> BaseResponse[OrderDetailRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_order_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Order not found")
        if user_id is not None and str(row.user_id) != user_id:
            raise HTTPException(status_code=404, detail="Order not found")
        items = await self._read_items(parsed_id)
        return BaseResponse[OrderDetailRead](
            status_code=200,
            message="Successful",
            data=_to_detail_read(row, items),
        )


class WritableOrderService(writable_service(OrderService)):
    pass


class ReadableOrderService(readable_service(OrderService)):
    pass

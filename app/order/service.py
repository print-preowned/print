from __future__ import annotations

import math
import uuid
from decimal import Decimal

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.order.model import OrderCreateRequest, OrderUpdateRequest
from app.order.repository import (
    count_orders,
    create_order,
    list_orders,
    read_order_by_id,
    soft_delete_order,
    update_order,
)
from app.order.schemas import OrderCreate, OrderRead, OrderUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> OrderRead:
    return OrderRead.model_validate(row)


def _to_create(payload: OrderCreateRequest) -> OrderCreate:
    data = payload.model_dump(include=set(OrderCreate.model_fields.keys()))
    data["user_id"] = _parse_id(str(data["user_id"]))
    data["total_amount"] = Decimal(str(data["total_amount"]))
    return OrderCreate.model_validate(data)


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, order: OrderCreateRequest) -> Response:
        await create_order(self._session, _to_create(order))
        return Response(status_code=201)

    async def update(self, id: str, order: OrderUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        update_data = order.model_dump(exclude_unset=True)
        if "user_id" in update_data and update_data["user_id"] is not None:
            update_data["user_id"] = _parse_id(str(update_data["user_id"]))
        if "total_amount" in update_data and update_data["total_amount"] is not None:
            update_data["total_amount"] = Decimal(str(update_data["total_amount"]))

        updated = await update_order(
            self._session,
            parsed_id,
            OrderUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await soft_delete_order(self._session, parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Order not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[OrderRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await count_orders(self._session)
        rows = await list_orders(self._session, offset=offset, limit=size)
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

    async def read_by_id(self, id: str) -> BaseResponse[OrderRead]:
        parsed_id = _parse_id(id)
        row = await read_order_by_id(self._session, parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return BaseResponse[OrderRead](status_code=200, message="Successful", data=_to_read(row))


from app.utility.service_deps import readable_service, writable_service

WritableOrderService = writable_service(OrderService)
ReadableOrderService = readable_service(OrderService)

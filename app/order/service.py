from __future__ import annotations

import math
import uuid
from decimal import Decimal

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.order.model import OrderCreateRequest, OrderUpdateRequest
from app.order.repository import OrderRepository
from app.order.schemas import OrderCreate, OrderRead, OrderUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


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
        self._repo = OrderRepository(session)

    async def create(self, order: OrderCreateRequest) -> Response:
        await self._repo.create_order(_to_create(order))
        return Response(status_code=201)

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

    async def read_by_id(self, id: str) -> BaseResponse[OrderRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_order_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return BaseResponse[OrderRead](status_code=200, message="Successful", data=_to_read(row))


class WritableOrderService(writable_service(OrderService)):
    pass


class ReadableOrderService(readable_service(OrderService)):
    pass

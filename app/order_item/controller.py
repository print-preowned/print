from fastapi import APIRouter, Depends, Response

from app.order_item.model import OrderItemCreateRequest, OrderItemUpdateRequest
from app.order_item.schemas import OrderItemRead
from app.order_item.service import ReadableOrderItemService, WritableOrderItemService
from app.utility.authorization import TokenPayload, require_context
from app.utility.model import BaseResponse

router = APIRouter(prefix="/orders/{order_id}/items", tags=["order-items"])


@router.post("", status_code=201)
async def create(
    order_id: str,
    payload: OrderItemCreateRequest,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableOrderItemService = Depends(),
) -> Response:
    return await service.create(order_id, payload)


@router.patch("/{id}")
async def update(
    order_id: str,
    id: str,
    payload: OrderItemUpdateRequest,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableOrderItemService = Depends(),
) -> Response:
    return await service.update(order_id, id, payload)


@router.delete("/{id}")
async def delete(
    order_id: str,
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableOrderItemService = Depends(),
) -> Response:
    return await service.delete(order_id, id)


@router.get("/{id}")
async def read_by_id(
    order_id: str,
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: ReadableOrderItemService = Depends(),
) -> BaseResponse[OrderItemRead]:
    return await service.read_by_id(order_id, id)

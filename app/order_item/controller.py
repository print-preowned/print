from fastapi import APIRouter, Depends, Response

from app.order_item.model import OrderItemCreateRequest, OrderItemUpdateRequest
from app.order_item.schemas import OrderItemRead
from app.order_item.service import ReadableOrderItemService, WritableOrderItemService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/order-item", tags=["OrderItemController"])


@router.post("/create")
async def create(
    payload: OrderItemCreateRequest,
    service: WritableOrderItemService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: OrderItemUpdateRequest,
    service: WritableOrderItemService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableOrderItemService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableOrderItemService = Depends(),
) -> PaginatedResponse[OrderItemRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableOrderItemService = Depends(),
) -> BaseResponse[OrderItemRead]:
    return await service.read_by_id(id)

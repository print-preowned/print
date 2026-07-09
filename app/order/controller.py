from fastapi import APIRouter, Depends, Response

from app.order.model import OrderCreateRequest, OrderUpdateRequest
from app.order.schemas import OrderRead
from app.order.service import ReadableOrderService, WritableOrderService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/order", tags=["OrderController"])


@router.post("/create")
async def create(
    payload: OrderCreateRequest,
    service: WritableOrderService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: OrderUpdateRequest,
    service: WritableOrderService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableOrderService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableOrderService = Depends(),
) -> PaginatedResponse[OrderRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableOrderService = Depends(),
) -> BaseResponse[OrderRead]:
    return await service.read_by_id(id)

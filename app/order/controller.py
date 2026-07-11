from fastapi import APIRouter, Depends, Response

from app.order.model import OrderCreateRequest, OrderUpdateRequest
from app.order.schemas import OrderRead
from app.order.service import ReadableOrderService, WritableOrderService
from app.utility.authorization import TokenPayload, require_context, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", status_code=201)
async def create(
    payload: OrderCreateRequest,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableOrderService = Depends(),
) -> Response:
    return await service.create(payload)


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: ReadableOrderService = Depends(),
) -> BaseResponse[OrderRead]:
    return await service.read_by_id(id)


@router.get("")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_ORDER")),
    service: ReadableOrderService = Depends(),
) -> PaginatedResponse[OrderRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.patch("/{id}")
async def update(
    id: str,
    payload: OrderUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_ORDER")),
    service: WritableOrderService = Depends(),
) -> Response:
    return await service.update(id, payload)

from fastapi import APIRouter, Depends, HTTPException, Response

from app.order.model import OrderCreateRequest, OrderStatusUpdateRequest
from app.order.schemas import BusinessOrderDetailRead, BusinessOrderSummaryRead, OrderDetailRead
from app.order.service import ReadableOrderService, WritableOrderService
from app.utility.authorization import TokenPayload, get_business_id, require_context, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/orders", tags=["orders"])
business_router = APIRouter(prefix="/business-orders", tags=["business-orders"])


def _business_id(token: TokenPayload) -> str:
    business_id = get_business_id(token)
    if not business_id:
        raise HTTPException(status_code=403, detail="Business context required")
    return business_id


@router.post("", status_code=201)
async def create(
    payload: OrderCreateRequest,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableOrderService = Depends(),
) -> BaseResponse[OrderDetailRead]:
    return await service.create(payload, user_id=token.sub)


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: ReadableOrderService = Depends(),
) -> BaseResponse[OrderDetailRead]:
    return await service.read_by_id(id, user_id=token.sub)


@router.post("/{id}/cancel", status_code=204)
async def cancel_by_customer(
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableOrderService = Depends(),
) -> Response:
    return await service.cancel_by_customer(id, user_id=token.sub)


@business_router.get("")
async def read_for_business(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_ORDER")),
    service: ReadableOrderService = Depends(),
) -> PaginatedResponse[BusinessOrderSummaryRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read_for_business(_business_id(token), param)


@business_router.get("/{id}")
async def read_by_id_for_business(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_ORDER")),
    service: ReadableOrderService = Depends(),
) -> BaseResponse[BusinessOrderDetailRead]:
    return await service.read_by_id_for_business(id, _business_id(token))


@business_router.patch("/{id}/status", status_code=204)
async def update_status_for_business(
    id: str,
    payload: OrderStatusUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_ORDER")),
    service: WritableOrderService = Depends(),
) -> Response:
    return await service.update_status_for_business(id, _business_id(token), payload)

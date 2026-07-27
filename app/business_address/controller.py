from fastapi import APIRouter, Depends, HTTPException, Response

from app.business_address.model import BusinessAddressCreateRequest, BusinessAddressUpdateRequest
from app.business_address.schemas import BusinessAddressRead
from app.business_address.service import ReadableBusinessAddressService, WritableBusinessAddressService
from app.utility.authorization import TokenPayload, get_business_id, require_context, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/business-addresses", tags=["business-addresses"])
customer_router = APIRouter(prefix="/businesses/{business_id}/pickup-location", tags=["pickup-location"])


def _business_id(token: TokenPayload) -> str:
    business_id = get_business_id(token)
    if not business_id:
        raise HTTPException(status_code=403, detail="Business context required")
    return business_id


@router.get("")
async def read_for_business(
    page: int = 1,
    size: int = 10,
    search: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_BUSINESS")),
    service: ReadableBusinessAddressService = Depends(),
) -> PaginatedResponse[BusinessAddressRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(_business_id(token), param)


@router.post("", status_code=201)
async def create(
    payload: BusinessAddressCreateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_BUSINESS")),
    service: WritableBusinessAddressService = Depends(),
) -> BaseResponse[BusinessAddressRead]:
    return await service.create(payload, _business_id(token))


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_BUSINESS")),
    service: ReadableBusinessAddressService = Depends(),
) -> BaseResponse[BusinessAddressRead]:
    return await service.read_by_id(id, _business_id(token))


@router.patch("/{id}")
async def update(
    id: str,
    payload: BusinessAddressUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_BUSINESS")),
    service: WritableBusinessAddressService = Depends(),
) -> BaseResponse[BusinessAddressRead]:
    return await service.update(id, payload, _business_id(token))


@router.delete("/{id}", status_code=204)
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("UPDATE_BUSINESS")),
    service: WritableBusinessAddressService = Depends(),
) -> Response:
    return await service.delete(id, _business_id(token))


@router.post("/{id}/set-primary", status_code=204)
async def set_primary(
    id: str,
    token: TokenPayload = Depends(require_privilege("UPDATE_BUSINESS")),
    service: WritableBusinessAddressService = Depends(),
) -> Response:
    return await service.set_primary(id, _business_id(token))


@customer_router.get("")
async def read_pickup_location(
    business_id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: ReadableBusinessAddressService = Depends(),
) -> BaseResponse[BusinessAddressRead]:
    return await service.read_pickup_location_for_customer(business_id)

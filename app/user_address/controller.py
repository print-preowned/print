from fastapi import APIRouter, Depends, Response

from app.user_address.model import UserAddressCreateRequest, UserAddressUpdateRequest
from app.user_address.schemas import UserAddressRead
from app.user_address.service import ReadableUserAddressService, WritableUserAddressService
from app.utility.authorization import TokenPayload, require_context
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, pagination_params

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("", tags=["client"])
async def read_for_user(
    params: PaginationParams = Depends(pagination_params),
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: ReadableUserAddressService = Depends(),
) -> PaginatedResponse[UserAddressRead]:
    return await service.read(token.sub, params)


@router.post("", status_code=201, tags=["client"])
async def create(
    payload: UserAddressCreateRequest,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableUserAddressService = Depends(),
) -> BaseResponse[UserAddressRead]:
    return await service.create(payload, token.sub)


@router.get("/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: ReadableUserAddressService = Depends(),
) -> BaseResponse[UserAddressRead]:
    return await service.read_by_id(id, token.sub)


@router.patch("/{id}", tags=["client"])
async def update(
    id: str,
    payload: UserAddressUpdateRequest,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableUserAddressService = Depends(),
) -> BaseResponse[UserAddressRead]:
    return await service.update(id, payload, token.sub)


@router.delete("/{id}", status_code=204, tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableUserAddressService = Depends(),
) -> Response:
    return await service.delete(id, token.sub)


@router.post("/{id}/set-default", status_code=204, tags=["client"])
async def set_default(
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableUserAddressService = Depends(),
) -> Response:
    return await service.set_default(id, token.sub)

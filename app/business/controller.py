from fastapi import APIRouter, Depends, HTTPException, Response

from app.business.model import BusinessCreateRequest, BusinessCreateResponse, BusinessUpdateRequest
from app.business.schemas import BusinessRead
from app.business.service import ReadableBusinessService, WritableBusinessService
from app.utility.authorization import (
    TokenPayload,
    get_business_id,
    get_token_payload,
    require_context,
    require_owner,
)
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post("", status_code=201, tags=["client"])
async def create(
    payload: BusinessCreateRequest,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableBusinessService = Depends(),
) -> BusinessCreateResponse:
    return await service.create(payload, token.sub)


@router.patch("/{id}", tags=["client"])
async def update(
    id: str,
    payload: BusinessUpdateRequest,
    token: TokenPayload = Depends(require_owner()),
    service: WritableBusinessService = Depends(),
) -> Response:
    business_id = get_business_id(token)
    if business_id != id:
        raise HTTPException(status_code=403, detail="Can only update your own business")
    return await service.update(id, payload)


@router.delete("/{id}", tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_owner()),
    service: WritableBusinessService = Depends(),
) -> Response:
    business_id = get_business_id(token)
    if business_id != id:
        raise HTTPException(status_code=403, detail="Can only delete your own business")
    return await service.delete(id)


@router.get("", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: ReadableBusinessService = Depends(),
) -> PaginatedResponse[BusinessRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/me", tags=["client"])
async def read_by_user(
    token: TokenPayload = Depends(get_token_payload),
    service: ReadableBusinessService = Depends(),
) -> BaseResponse[BusinessRead | None]:
    return await service.read_by_user_id(token.sub)


@router.get("/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: ReadableBusinessService = Depends(),
) -> BaseResponse[BusinessRead]:
    return await service.read_by_id(id)

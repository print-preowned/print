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

router = APIRouter(prefix="/business", tags=["BusinessController"])


@router.post("/create", status_code=201, tags=["client"])
async def create(
    payload: BusinessCreateRequest,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableBusinessService = Depends(),
) -> BusinessCreateResponse:
    return await service.create(payload, token.sub)


@router.put("/update/{id}", tags=["client"])
async def update(
    id: str,
    payload: BusinessUpdateRequest,
    token: TokenPayload = Depends(require_owner()),
    service: WritableBusinessService = Depends(),
) -> Response:
    """
    Update a business

    Following MDC-OWNER-3: Requires BUSINESS context and owner status
    """
    business_id = get_business_id(token)
    if business_id != id:
        raise HTTPException(status_code=403, detail="Can only update your own business")

    return await service.update(id, payload)


@router.delete("/delete/{id}", tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_owner()),
    service: WritableBusinessService = Depends(),
) -> Response:
    """
    Delete a business

    Following MDC-OWNER-3: DELETE_BUSINESS requires owner status
    """
    business_id = get_business_id(token)
    if business_id != id:
        raise HTTPException(status_code=403, detail="Can only delete your own business")

    return await service.delete(id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: ReadableBusinessService = Depends(),
) -> PaginatedResponse[BusinessRead]:
    """
    Read businesses (paginated)

    Requires BUSINESS context - users can read businesses they're part of
    """
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: ReadableBusinessService = Depends(),
) -> BaseResponse[BusinessRead]:
    """
    Read a business by ID

    Requires BUSINESS context
    """
    return await service.read_by_id(id)


@router.get("/read/by-user-id", tags=["client"])
async def read_by_user(
    token: TokenPayload = Depends(get_token_payload),
    service: ReadableBusinessService = Depends(),
) -> BaseResponse[BusinessRead | None]:
    """
    Check if the current user has a business

    Can be called from any context (CUSTOMER or BUSINESS)
    Returns the business if found, None otherwise
    """
    return await service.read_by_user_id(token.sub)

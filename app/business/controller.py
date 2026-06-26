from app.business.model import Business, BusinessCreateRequest, BusinessCreateResponse, BusinessUpdateRequest
from .service import (
    delete_service,
    read_service,
    read_by_id_service,
    create_service,
    update_service,
    read_by_user_id_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest, PyObjectId
from ..utility.authorization import (
    require_context,
    require_owner,
    TokenPayload,
    get_business_id,
    get_token_payload,
)
from fastapi import APIRouter, Response, Depends, Request, HTTPException

router = APIRouter(prefix="/business", tags=["BusinessController"])


@router.post("/create", status_code=201, tags=["client"])
async def create(
    payload: BusinessCreateRequest,
    request: Request,
    token: TokenPayload = Depends(require_context("CUSTOMER"))
) -> BusinessCreateResponse:
    return await create_service(payload, token.sub)


@router.put("/update/{id}", tags=["client"])
async def update(
    id: str,
    payload: BusinessUpdateRequest,
    token: TokenPayload = Depends(require_owner())
) -> Response:
    """
    Update a business
    
    Following MDC-OWNER-3: Requires BUSINESS context and owner status
    """
    # Ensure user can only update their own business
    business_id = get_business_id(token)
    if business_id != id:
        raise HTTPException(status_code=403, detail="Can only update your own business")
    
    return await update_service(id, payload)


@router.delete("/delete/{id}", tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_owner())
) -> Response:
    """
    Delete a business
    
    Following MDC-OWNER-3: DELETE_BUSINESS requires owner status
    """
    # Ensure user can only delete their own business
    business_id = get_business_id(token)
    if business_id != id:
        raise HTTPException(status_code=403, detail="Can only delete your own business")
    
    return await delete_service(id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("BUSINESS"))
) -> PaginatedResponse[Business]:
    """
    Read businesses (paginated)
    
    Requires BUSINESS context - users can read businesses they're part of
    """
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("BUSINESS"))
) -> BaseResponse[Business]:
    """
    Read a business by ID
    
    Requires BUSINESS context
    """
    return await read_by_id_service(id)


@router.get("/read/by-user-id", tags=["client"])
async def read_by_user(
    token: TokenPayload = Depends(get_token_payload)
) -> BaseResponse[Business | None]:
    """
    Check if the current user has a business
    
    Can be called from any context (CUSTOMER or BUSINESS)
    Returns the business if found, None otherwise
    """
    return await read_by_user_id_service(token.sub)



from app.business_book.model import (
    BusinessBook,
    BusinessBookWithBook,
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
)
from .service import (
    delete_service,
    read_by_business_id_service,
    read_by_id_service,
    create_service,
    update_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from ..utility.authorization import require_context, TokenPayload, get_business_id
from fastapi import APIRouter, Response, Depends, HTTPException

router = APIRouter(prefix="/business-book", tags=["BusinessBookController"])


@router.post("/create", tags=["client"])
async def create(
    payload: BusinessBookCreateRequest,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> Response:
    business_id = get_business_id(token)
    if not business_id:
        raise HTTPException(status_code=403, detail="Business context required")
    return await create_service(payload, business_id)


@router.put("/update/{id}", tags=["client"])
async def update(
    id: str,
    payload: BusinessBookUpdateRequest,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> Response:
    business_id = get_business_id(token)
    if not business_id:
        raise HTTPException(status_code=403, detail="Business context required")
    return await update_service(id, payload, business_id)


@router.delete("/delete/{id}", tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> Response:
    business_id = get_business_id(token)
    if not business_id:
        raise HTTPException(status_code=403, detail="Business context required")
    return await delete_service(id, business_id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> PaginatedResponse[BusinessBookWithBook]:
    business_id = get_business_id(token)
    if not business_id:
        raise HTTPException(status_code=403, detail="Business context required")
    param = ParamRequest(page=page, size=size, search=search)
    return await read_by_business_id_service(business_id, param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> BaseResponse[BusinessBook]:
    business_id = get_business_id(token)
    return await read_by_id_service(id, business_id)



from app.business_book.model import (
    BusinessBookWithVariants,
    BusinessBookWithVariantSummary,
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
)
from app.variant.model import (
    VariantCreateRequest,
    VariantUpdateRequest,
    VariantWithConfig,
)
from .service import (
    delete_service,
    read_by_business_id_service,
    read_by_id_service,
    create_service,
    update_service,
)
from app.variant.service import (
    create_service as variant_create_service,
    delete_service as variant_delete_service,
    read_scoped_service,
    update_service as variant_update_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from ..utility.authorization import require_context, TokenPayload, get_business_id
from fastapi import APIRouter, Response, Depends, HTTPException

router = APIRouter(prefix="/business-book", tags=["BusinessBookController"])


def _require_business_id(token: TokenPayload) -> str:
    business_id = get_business_id(token)
    if not business_id:
        raise HTTPException(status_code=403, detail="Business context required")
    return business_id


@router.post("/create", tags=["client"])
async def create(
    payload: BusinessBookCreateRequest,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> Response:
    business_id = _require_business_id(token)
    return await create_service(payload, business_id)


@router.put("/update/{id}", tags=["client"])
async def update(
    id: str,
    payload: BusinessBookUpdateRequest,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> Response:
    business_id = _require_business_id(token)
    return await update_service(id, payload, business_id)


@router.delete("/delete/{id}", tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> Response:
    business_id = _require_business_id(token)
    return await delete_service(id, business_id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> PaginatedResponse[BusinessBookWithVariantSummary]:
    business_id = _require_business_id(token)
    param = ParamRequest(page=page, size=size, search=search)
    return await read_by_business_id_service(business_id, param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> BaseResponse[BusinessBookWithVariants]:
    business_id = _require_business_id(token)
    return await read_by_id_service(id, business_id)


@router.get("/{business_book_id}/variant", tags=["client"])
async def read_variants(
    business_book_id: str,
    page: int = 1,
    size: int = 5,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> PaginatedResponse[VariantWithConfig]:
    business_id = _require_business_id(token)
    param = ParamRequest(page=page, size=size)
    return await read_scoped_service(business_book_id, param, business_id)


@router.post("/{business_book_id}/variant", tags=["client"])
async def create_variant(
    business_book_id: str,
    payload: VariantCreateRequest,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> BaseResponse[dict]:
    business_id = _require_business_id(token)
    return await variant_create_service(business_book_id, payload, business_id)


@router.put("/{business_book_id}/variant/{variant_id}", tags=["client"])
async def update_variant(
    business_book_id: str,
    variant_id: str,
    payload: VariantUpdateRequest,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> Response:
    business_id = _require_business_id(token)
    return await variant_update_service(business_book_id, variant_id, payload, business_id)


@router.delete("/{business_book_id}/variant/{variant_id}", tags=["client"])
async def delete_variant(
    business_book_id: str,
    variant_id: str,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> Response:
    business_id = _require_business_id(token)
    return await variant_delete_service(business_book_id, variant_id, business_id)

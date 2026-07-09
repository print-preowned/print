from fastapi import APIRouter, Depends, HTTPException, Response

from app.business_book.model import (
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
    BusinessBookWithVariants,
    BusinessBookWithVariantSummary,
)
from app.business_book.service import ReadableBusinessBookService, WritableBusinessBookService
from app.utility.authorization import TokenPayload, get_business_id, require_context
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest
from app.variant.model import VariantCreateRequest, VariantUpdateRequest, VariantWithConfig
from app.variant.service import ReadableVariantService, WritableVariantService

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
    service: WritableBusinessBookService = Depends(),
) -> Response:
    business_id = _require_business_id(token)
    return await service.create(payload, business_id)


@router.put("/update/{id}", tags=["client"])
async def update(
    id: str,
    payload: BusinessBookUpdateRequest,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: WritableBusinessBookService = Depends(),
) -> Response:
    business_id = _require_business_id(token)
    return await service.update(id, payload, business_id)


@router.delete("/delete/{id}", tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: WritableBusinessBookService = Depends(),
) -> Response:
    business_id = _require_business_id(token)
    return await service.delete(id, business_id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: ReadableBusinessBookService = Depends(),
) -> PaginatedResponse[BusinessBookWithVariantSummary]:
    business_id = _require_business_id(token)
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read_by_business_id(business_id, param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: ReadableBusinessBookService = Depends(),
) -> BaseResponse[BusinessBookWithVariants]:
    business_id = _require_business_id(token)
    return await service.read_by_id(id, business_id)


@router.get("/{business_book_id}/variant", tags=["client"])
async def read_variants(
    business_book_id: str,
    page: int = 1,
    size: int = 5,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: ReadableVariantService = Depends(),
) -> PaginatedResponse[VariantWithConfig]:
    business_id = _require_business_id(token)
    param = ParamRequest(page=page, size=size)
    return await service.read_scoped(business_book_id, param, business_id)


@router.post("/{business_book_id}/variant", tags=["client"])
async def create_variant(
    business_book_id: str,
    payload: VariantCreateRequest,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: WritableVariantService = Depends(),
) -> BaseResponse[dict]:
    business_id = _require_business_id(token)
    return await service.create(business_book_id, payload, business_id)


@router.put("/{business_book_id}/variant/{variant_id}", tags=["client"])
async def update_variant(
    business_book_id: str,
    variant_id: str,
    payload: VariantUpdateRequest,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: WritableVariantService = Depends(),
) -> Response:
    business_id = _require_business_id(token)
    return await service.update(business_book_id, variant_id, payload, business_id)


@router.delete("/{business_book_id}/variant/{variant_id}", tags=["client"])
async def delete_variant(
    business_book_id: str,
    variant_id: str,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: WritableVariantService = Depends(),
) -> Response:
    business_id = _require_business_id(token)
    return await service.delete(business_book_id, variant_id, business_id)

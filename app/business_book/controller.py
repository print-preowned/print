from fastapi import APIRouter, Depends, HTTPException, Response

from app.business_book.model import (
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
    BusinessBookWithVariants,
    BusinessBookWithVariantSummary,
)
from app.business_book.service import ReadableBusinessBookService, WritableBusinessBookService
from app.utility.authorization import TokenPayload, get_business_id, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest
from app.variant.model import VariantCreateRequest, VariantUpdateRequest
from app.variant.schemas import VariantWithConfigRead
from app.variant.service import ReadableVariantService, WritableVariantService

router = APIRouter(prefix="/business-books", tags=["business-books"])


def _business_id(token: TokenPayload) -> str:
    business_id = get_business_id(token)
    if not business_id:
        raise HTTPException(status_code=403, detail="Business context required")
    return business_id


@router.post("", status_code=201, tags=["client"])
async def create(
    payload: BusinessBookCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_BUSINESS_BOOK")),
    service: WritableBusinessBookService = Depends(),
) -> Response:
    return await service.create(payload, _business_id(token))


@router.patch("/{id}", tags=["client"])
async def update(
    id: str,
    payload: BusinessBookUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_BUSINESS_BOOK")),
    service: WritableBusinessBookService = Depends(),
) -> Response:
    return await service.update(id, payload, _business_id(token))


@router.delete("/{id}", tags=["client"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_BUSINESS_BOOK")),
    service: WritableBusinessBookService = Depends(),
) -> Response:
    return await service.delete(id, _business_id(token))


@router.get("", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_BUSINESS_BOOK")),
    service: ReadableBusinessBookService = Depends(),
) -> PaginatedResponse[BusinessBookWithVariantSummary]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read_by_business_id(_business_id(token), param)


@router.get("/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_BUSINESS_BOOK")),
    service: ReadableBusinessBookService = Depends(),
) -> BaseResponse[BusinessBookWithVariants]:
    return await service.read_by_id(id, _business_id(token))


@router.get("/{business_book_id}/variants", tags=["client"])
async def read_variants(
    business_book_id: str,
    page: int = 1,
    size: int = 5,
    token: TokenPayload = Depends(require_privilege("READ_VARIANT")),
    service: ReadableVariantService = Depends(),
) -> PaginatedResponse[VariantWithConfigRead]:
    param = ParamRequest(page=page, size=size)
    return await service.read_scoped(business_book_id, param, _business_id(token))


@router.post("/{business_book_id}/variants", status_code=201, tags=["client"])
async def create_variant(
    business_book_id: str,
    payload: VariantCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_VARIANT")),
    service: WritableVariantService = Depends(),
) -> BaseResponse[dict]:
    return await service.create(business_book_id, payload, _business_id(token))


@router.patch("/{business_book_id}/variants/{variant_id}", tags=["client"])
async def update_variant(
    business_book_id: str,
    variant_id: str,
    payload: VariantUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_VARIANT")),
    service: WritableVariantService = Depends(),
) -> Response:
    return await service.update(business_book_id, variant_id, payload, _business_id(token))


@router.delete("/{business_book_id}/variants/{variant_id}", tags=["client"])
async def delete_variant(
    business_book_id: str,
    variant_id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_VARIANT")),
    service: WritableVariantService = Depends(),
) -> Response:
    return await service.delete(business_book_id, variant_id, _business_id(token))

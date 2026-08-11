from fastapi import APIRouter, Depends, HTTPException, Response

from app.business_book.model import (
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
    BusinessBookWithVariants,
    BusinessBookWithVariantSummary,
    PublicCatalogBusinessBookDetail,
    PublicCatalogBusinessBookRead,
)
from app.business_book.service import ReadableBusinessBookService, WritableBusinessBookService
from app.utility.authorization import (
    TokenPayload,
    get_business_id,
    require_privilege,
)
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, pagination_params_with
from app.variant.model import VariantCreateRequest, VariantUpdateRequest
from app.variant.schemas import VariantWithConfigRead
from app.variant.service import ReadableVariantService, WritableVariantService

router = APIRouter(prefix="/business-books", tags=["business-books"])
customer_router = APIRouter(tags=["public-catalog"])


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
async def read_seller_inventory(
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    token: TokenPayload = Depends(require_privilege("READ_BUSINESS_BOOK")),
    service: ReadableBusinessBookService = Depends(),
) -> PaginatedResponse[BusinessBookWithVariantSummary]:
    return await service.read_by_business_id(_business_id(token), params)


@customer_router.get("/books/{book_id}/offers", tags=["client"])
async def read_book_offers(
    book_id: str,
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    exclude_id: str | None = None,
    service: ReadableBusinessBookService = Depends(),
) -> PaginatedResponse[PublicCatalogBusinessBookRead]:
    return await service.read_public_catalog(
        params,
        book_id=book_id,
        exclude_id=exclude_id,
    )


@customer_router.get("/businesses/{business_id}/storefront/catalog", tags=["client"])
async def read_storefront_catalog(
    business_id: str,
    params: PaginationParams = Depends(pagination_params_with(default_size=20)),
    service: ReadableBusinessBookService = Depends(),
) -> PaginatedResponse[PublicCatalogBusinessBookRead]:
    return await service.read_public_store_catalog(business_id, params)


@customer_router.get("/offers/{id}", tags=["client"])
async def read_public_offer(
    id: str,
    service: ReadableBusinessBookService = Depends(),
) -> BaseResponse[PublicCatalogBusinessBookDetail]:
    return await service.read_public_by_id(id)


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
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    token: TokenPayload = Depends(require_privilege("READ_VARIANT")),
    service: ReadableVariantService = Depends(),
) -> PaginatedResponse[VariantWithConfigRead]:
    return await service.read_scoped(business_book_id, params, _business_id(token))


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

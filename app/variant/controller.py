from app.variant.model import (
    Variant,
    PublicCatalogVariant,
)
from .service import (
    read_service,
    read_by_id_service,
    read_public_catalog_service,
    read_public_catalog_by_id_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from ..utility.authorization import require_context, require_privilege, TokenPayload
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/variant", tags=["VariantController"])
catalog_router = APIRouter(prefix="/inventory", tags=["InventoryCatalogController"])


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    _: TokenPayload = Depends(require_privilege("VIEW_VARIANTS")),
) -> PaginatedResponse[Variant]:
    """Platform read-only audit view across all variants. Sellers use business-book scoped routes."""
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    _: TokenPayload = Depends(require_privilege("VIEW_VARIANTS")),
) -> BaseResponse[Variant]:
    """Platform read-only variant detail. Moderation actions belong on business_book listings."""
    return await read_by_id_service(id)


@catalog_router.get("/read", tags=["client"])
async def read_public_catalog(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
) -> PaginatedResponse[PublicCatalogVariant]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_public_catalog_service(param)


@catalog_router.get("/read/by-id/{id}", tags=["client"])
async def read_public_catalog_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
) -> BaseResponse[PublicCatalogVariant]:
    return await read_public_catalog_by_id_service(id)

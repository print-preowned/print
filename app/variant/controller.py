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
from app.auth.privilege_catalog import Privilege
from ..utility.authorization import require_context, require_privilege, TokenPayload
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/variants", tags=["VariantController"])


@router.get("/audit/read", tags=["platform"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    _: TokenPayload = Depends(require_privilege(Privilege.READ_VARIANT)),
) -> PaginatedResponse[Variant]:
    """Platform read-only audit view across all variants. Sellers use business-book scoped routes."""
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/audit/read/by-id/{id}", tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    _: TokenPayload = Depends(require_privilege(Privilege.READ_VARIANT)),
) -> BaseResponse[Variant]:
    """Platform read-only variant detail. Moderation actions belong on business_book listings."""
    return await read_by_id_service(id)


@router.get("/read", tags=["client"])
async def read_public_catalog(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
) -> PaginatedResponse[PublicCatalogVariant]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_public_catalog_service(param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_public_catalog_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
) -> BaseResponse[PublicCatalogVariant]:
    return await read_public_catalog_by_id_service(id)

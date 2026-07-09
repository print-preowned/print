from fastapi import APIRouter, Depends

from app.auth.privilege_catalog import Privilege
from app.variant.schemas import PublicCatalogVariantRead, VariantRead
from app.variant.service import ReadableVariantService
from app.utility.authorization import require_context, require_privilege, TokenPayload
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/variants", tags=["VariantController"])


@router.get("/audit/read", tags=["platform"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    _: TokenPayload = Depends(require_privilege(Privilege.READ_VARIANT)),
    service: ReadableVariantService = Depends(),
) -> PaginatedResponse[VariantRead]:
    """Platform read-only audit view across all variants. Sellers use business-book scoped routes."""
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/audit/read/by-id/{id}", tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    _: TokenPayload = Depends(require_privilege(Privilege.READ_VARIANT)),
    service: ReadableVariantService = Depends(),
) -> BaseResponse[VariantRead]:
    """Platform read-only variant detail. Moderation actions belong on business_book listings."""
    return await service.read_by_id(id)


@router.get("/read", tags=["client"])
async def read_public_catalog(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: ReadableVariantService = Depends(),
) -> PaginatedResponse[PublicCatalogVariantRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read_public_catalog(param)


@router.get("/read/by-id/{id}", tags=["client"])
async def read_public_catalog_by_id(
    id: str,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: ReadableVariantService = Depends(),
) -> BaseResponse[PublicCatalogVariantRead]:
    return await service.read_public_catalog_by_id(id)

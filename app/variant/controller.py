from fastapi import APIRouter, Depends, HTTPException

from app.auth.privilege_catalog import Privilege
from app.utility.authorization import (
    TokenPayload,
    get_optional_token_payload,
)
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, pagination_params_with
from app.variant.schemas import PublicCatalogVariantRead, VariantRead
from app.variant.service import ReadableVariantService

router = APIRouter(prefix="/variants", tags=["variants"])


def _assert_platform_read_variant(token: TokenPayload) -> None:
    if token.ctx != "PLATFORM":
        raise HTTPException(status_code=403, detail="PLATFORM context required")
    privileges = token.privileges
    if (
        Privilege.READ_VARIANT not in privileges
        and "MANAGE_VARIANTS" not in privileges
    ):
        raise HTTPException(status_code=403, detail="User unauthorized to access this resource")


@router.get("")
async def read(
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    book_id: str | None = None,
    token: TokenPayload | None = Depends(get_optional_token_payload),
    service: ReadableVariantService = Depends(),
) -> PaginatedResponse[VariantRead] | PaginatedResponse[PublicCatalogVariantRead]:
    if token is None or token.ctx in ("CUSTOMER", "BUSINESS"):
        return await service.read_public_catalog(params, book_id=book_id)
    if token.ctx == "PLATFORM":
        _assert_platform_read_variant(token)
        return await service.read(params)
    raise HTTPException(status_code=403, detail="Unsupported context for variant catalog")


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload | None = Depends(get_optional_token_payload),
    service: ReadableVariantService = Depends(),
) -> BaseResponse[VariantRead] | BaseResponse[PublicCatalogVariantRead]:
    if token is None or token.ctx in ("CUSTOMER", "BUSINESS"):
        return await service.read_public_catalog_by_id(id)
    if token.ctx == "PLATFORM":
        _assert_platform_read_variant(token)
        return await service.read_by_id(id)
    raise HTTPException(status_code=403, detail="Unsupported context for variant catalog")

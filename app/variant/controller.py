from app.variant.model import (
    Variant,
    VariantCreateRequest,
    VariantUpdateRequest,
    PublicCatalogVariant,
)
from .service import (
    delete_service,
    read_service,
    read_by_id_service,
    read_public_catalog_service,
    read_public_catalog_by_id_service,
    create_service,
    update_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from ..utility.authorization import require_context, TokenPayload
from fastapi import APIRouter, Response, Depends

router = APIRouter(prefix="/variant", tags=["VariantController"])
catalog_router = APIRouter(prefix="/inventory", tags=["InventoryCatalogController"])


@router.post("/create")
async def create(payload: VariantCreateRequest) -> Response:
    return await create_service(payload)


@router.put("/update/{id}")
async def update(id: str, payload: VariantUpdateRequest) -> Response:
    return await update_service(id, payload)


@router.delete("/delete/{id}")
async def delete(id) -> Response:
    return await delete_service(id)


@router.get("/read")
async def read(
    page: int = 1, size: int = 5, search: str | None = None
) -> PaginatedResponse[Variant]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}")
async def read_by_id(id: str) -> BaseResponse[Variant]:
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

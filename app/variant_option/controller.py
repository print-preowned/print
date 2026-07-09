from fastapi import APIRouter, Depends, Response

from app.variant_option.model import VariantOptionCreateRequest, VariantOptionUpdateRequest
from app.variant_option.schemas import ProductOptionValueRead
from app.variant_option.service import ReadableVariantOptionService, WritableVariantOptionService
from app.utility.authorization import TokenPayload, require_context
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/variant-option", tags=["VariantOptionController"])


@router.post("/create")
async def create(
    payload: VariantOptionCreateRequest,
    service: WritableVariantOptionService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: VariantOptionUpdateRequest,
    service: WritableVariantOptionService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableVariantOptionService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    variant_type_id: str | None = None,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: ReadableVariantOptionService = Depends(),
) -> PaginatedResponse[ProductOptionValueRead]:
    param = ParamRequest(page=page, size=size, search=search)
    if variant_type_id:
        return await service.read_by_variant_type(variant_type_id, param)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableVariantOptionService = Depends(),
) -> BaseResponse[ProductOptionValueRead]:
    return await service.read_by_id(id)

from fastapi import APIRouter, Depends, Response

from app.variant_type.model import VariantTypeCreateRequest, VariantTypeUpdateRequest
from app.variant_type.schemas import ProductOptionRead
from app.variant_type.service import ReadableVariantTypeService, WritableVariantTypeService
from app.utility.authorization import TokenPayload, require_context
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/variant-type", tags=["VariantTypeController"])


@router.post("/create")
async def create(
    payload: VariantTypeCreateRequest,
    service: WritableVariantTypeService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: VariantTypeUpdateRequest,
    service: WritableVariantTypeService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableVariantTypeService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("BUSINESS")),
    service: ReadableVariantTypeService = Depends(),
) -> PaginatedResponse[ProductOptionRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableVariantTypeService = Depends(),
) -> BaseResponse[ProductOptionRead]:
    return await service.read_by_id(id)

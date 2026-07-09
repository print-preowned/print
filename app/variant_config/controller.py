from fastapi import APIRouter, Depends, Response

from app.variant_config.model import VariantConfigCreateRequest, VariantConfigUpdateRequest
from app.variant_config.schemas import VariantProductOptionValueRead
from app.variant_config.service import ReadableVariantConfigService, WritableVariantConfigService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/variant-config", tags=["VariantConfigController"])


@router.post("/create")
async def create(
    payload: VariantConfigCreateRequest,
    service: WritableVariantConfigService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: VariantConfigUpdateRequest,
    service: WritableVariantConfigService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableVariantConfigService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableVariantConfigService = Depends(),
) -> PaginatedResponse[VariantProductOptionValueRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableVariantConfigService = Depends(),
) -> BaseResponse[VariantProductOptionValueRead]:
    return await service.read_by_id(id)

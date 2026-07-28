from fastapi import APIRouter, Depends, Response

from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, pagination_params_with
from app.variant_config.model import VariantConfigCreateRequest, VariantConfigUpdateRequest
from app.variant_config.schemas import VariantProductOptionValueRead
from app.variant_config.service import ReadableVariantConfigService, WritableVariantConfigService

router = APIRouter(prefix="/variant-configs", tags=["variant-configs"])


@router.post("", status_code=201)
async def create(
    payload: VariantConfigCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_VARIANT_CONFIG")),
    service: WritableVariantConfigService = Depends(),
) -> Response:
    return await service.create(payload)


@router.patch("/{id}")
async def update(
    id: str,
    payload: VariantConfigUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_VARIANT_CONFIG")),
    service: WritableVariantConfigService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/{id}")
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_VARIANT_CONFIG")),
    service: WritableVariantConfigService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("")
async def read(
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    token: TokenPayload = Depends(require_privilege("READ_VARIANT_CONFIG")),
    service: ReadableVariantConfigService = Depends(),
) -> PaginatedResponse[VariantProductOptionValueRead]:
    return await service.read(params)


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_VARIANT_CONFIG")),
    service: ReadableVariantConfigService = Depends(),
) -> BaseResponse[VariantProductOptionValueRead]:
    return await service.read_by_id(id)

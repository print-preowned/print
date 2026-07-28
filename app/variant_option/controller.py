from fastapi import APIRouter, Depends, Response

from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, pagination_params_with
from app.variant_option.model import VariantOptionCreateRequest, VariantOptionUpdateRequest
from app.variant_option.schemas import ProductOptionValueRead
from app.variant_option.service import ReadableVariantOptionService, WritableVariantOptionService

router = APIRouter(prefix="/variant-options", tags=["variant-options"])


@router.post("", status_code=201)
async def create(
    payload: VariantOptionCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_VARIANT_OPTION")),
    service: WritableVariantOptionService = Depends(),
) -> Response:
    return await service.create(payload)


@router.patch("/{id}")
async def update(
    id: str,
    payload: VariantOptionUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_VARIANT_OPTION")),
    service: WritableVariantOptionService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/{id}")
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_VARIANT_OPTION")),
    service: WritableVariantOptionService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("")
async def read(
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    variant_type_id: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_VARIANT_OPTION")),
    service: ReadableVariantOptionService = Depends(),
) -> PaginatedResponse[ProductOptionValueRead]:
    if variant_type_id:
        return await service.read_by_variant_type(variant_type_id, params)
    return await service.read(params)


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_VARIANT_OPTION")),
    service: ReadableVariantOptionService = Depends(),
) -> BaseResponse[ProductOptionValueRead]:
    return await service.read_by_id(id)

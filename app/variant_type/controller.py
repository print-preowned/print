from fastapi import APIRouter, Depends, Response

from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, pagination_params_with
from app.variant_type.model import VariantTypeCreateRequest, VariantTypeUpdateRequest
from app.variant_type.schemas import ProductOptionRead
from app.variant_type.service import ReadableVariantTypeService, WritableVariantTypeService

router = APIRouter(prefix="/variant-types", tags=["variant-types"])


@router.post("", status_code=201)
async def create(
    payload: VariantTypeCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_VARIANT_TYPE")),
    service: WritableVariantTypeService = Depends(),
) -> Response:
    return await service.create(payload)


@router.patch("/{id}")
async def update(
    id: str,
    payload: VariantTypeUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_VARIANT_TYPE")),
    service: WritableVariantTypeService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/{id}")
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_VARIANT_TYPE")),
    service: WritableVariantTypeService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("")
async def read(
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    token: TokenPayload = Depends(require_privilege("READ_VARIANT_TYPE")),
    service: ReadableVariantTypeService = Depends(),
) -> PaginatedResponse[ProductOptionRead]:
    return await service.read(params)


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_VARIANT_TYPE")),
    service: ReadableVariantTypeService = Depends(),
) -> BaseResponse[ProductOptionRead]:
    return await service.read_by_id(id)

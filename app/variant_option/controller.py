from app.variant_option.model import (
    VariantOption,
    VariantOptionCreateRequest,
    VariantOptionUpdateRequest,
)
from .service import (
    delete_service,
    read_service,
    read_by_variant_type_service,
    read_by_id_service,
    create_service,
    update_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from ..utility.authorization import require_context, TokenPayload
from fastapi import APIRouter, Response, Depends

router = APIRouter(prefix="/variant-option", tags=["VariantOptionController"])


@router.post("/create")
async def create(payload: VariantOptionCreateRequest) -> Response:
    return await create_service(payload)


@router.put("/update/{id}")
async def update(id: str, payload: VariantOptionUpdateRequest) -> Response:
    return await update_service(id, payload)


@router.delete("/delete/{id}")
async def delete(id) -> Response:
    return await delete_service(id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    variant_type_id: str | None = None,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> PaginatedResponse[VariantOption]:
    param = ParamRequest(page=page, size=size, search=search)
    if variant_type_id:
        return await read_by_variant_type_service(variant_type_id, param)
    return await read_service(param)


@router.get("/read/by-id/{id}")
async def read_by_id(id: str) -> BaseResponse[VariantOption]:
    return await read_by_id_service(id)



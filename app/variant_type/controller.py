from app.variant_type.model import (
    VariantType,
    VariantTypeCreateRequest,
    VariantTypeUpdateRequest,
)
from .service import (
    delete_service,
    read_service,
    read_by_id_service,
    create_service,
    update_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from ..utility.authorization import require_context, TokenPayload
from fastapi import APIRouter, Response, Depends

router = APIRouter(prefix="/variant-type", tags=["VariantTypeController"])


@router.post("/create")
async def create(payload: VariantTypeCreateRequest) -> Response:
    return await create_service(payload)


@router.put("/update/{id}")
async def update(id: str, payload: VariantTypeUpdateRequest) -> Response:
    return await update_service(id, payload)


@router.delete("/delete/{id}")
async def delete(id) -> Response:
    return await delete_service(id)


@router.get("/read", tags=["client"])
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_context("BUSINESS")),
) -> PaginatedResponse[VariantType]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}")
async def read_by_id(id: str) -> BaseResponse[VariantType]:
    return await read_by_id_service(id)



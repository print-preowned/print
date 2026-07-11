from fastapi import APIRouter, Depends, Response

from app.module.model import ModuleCreateRequest, ModuleDeleteRequest, ModuleUpdateRequest
from app.module.service import WritableModuleService
from app.utility.authorization import TokenPayload, require_context

router = APIRouter(prefix="/admin/modules", tags=["modules"])


@router.post("/bulk", status_code=201)
async def bulk_create(
    payload: ModuleCreateRequest,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableModuleService = Depends(),
) -> Response:
    return await service.create_module(payload)


@router.patch("/bulk")
async def bulk_update(
    payload: ModuleUpdateRequest,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableModuleService = Depends(),
) -> Response:
    return await service.update_module(payload)


@router.delete("/bulk")
async def bulk_delete(
    payload: ModuleDeleteRequest,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritableModuleService = Depends(),
) -> Response:
    return await service.delete_module(payload)

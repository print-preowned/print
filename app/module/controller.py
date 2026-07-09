from fastapi import APIRouter, Depends, Response

from app.module.model import ModuleCreateRequest, ModuleDeleteRequest, ModuleUpdateRequest
from app.module.service import WritableModuleService

router = APIRouter(prefix="/module", tags=["ModuleController"])


@router.post("/bulk-create")
async def bulk_create(
    payload: ModuleCreateRequest,
    service: WritableModuleService = Depends(),
) -> Response:
    """
    Create privileges and role_privilege mappings for a specified module.

    This endpoint allows you to:
    - Create multiple privileges for a module
    - Create multiple role_privilege mappings for the module

    All operations are performed for the specified module_name.
    """
    return await service.create_module(payload)


@router.put("/bulk-update")
async def bulk_update(
    payload: ModuleUpdateRequest,
    service: WritableModuleService = Depends(),
) -> Response:
    """
    Update privileges for a specified module.

    This endpoint allows you to update multiple privileges for a module.
    All operations are performed for the specified module_name.
    """
    return await service.update_module(payload)


@router.delete("/bulk-delete")
async def bulk_delete(
    payload: ModuleDeleteRequest,
    service: WritableModuleService = Depends(),
) -> Response:
    """
    Delete privileges and role_privilege mappings for a specified module.

    This endpoint allows you to:
    - Delete multiple privileges for a module
    - Delete multiple role_privilege mappings for the module

    All operations are performed for the specified module_name.
    """
    return await service.delete_module(payload)

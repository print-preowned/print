from app.module.model import ModuleCreateRequest, ModuleUpdateRequest, ModuleDeleteRequest
from .service import (
    create_module_service,
    update_module_service,
    delete_module_service,
)
from fastapi import APIRouter, Response

router = APIRouter(prefix="/module", tags=["ModuleController"])


@router.post("/bulk-create")
async def bulk_create(payload: ModuleCreateRequest) -> Response:
    """
    Create privileges and role_privilege mappings for a specified module.
    
    This endpoint allows you to:
    - Create multiple privileges for a module
    - Create multiple role_privilege mappings for the module
    
    All operations are performed for the specified module_name.
    """
    return await create_module_service(payload)


@router.put("/bulk-update")
async def bulk_update(payload: ModuleUpdateRequest) -> Response:
    """
    Update privileges for a specified module.
    
    This endpoint allows you to update multiple privileges for a module.
    All operations are performed for the specified module_name.
    """
    return await update_module_service(payload)


@router.delete("/bulk-delete")
async def bulk_delete(payload: ModuleDeleteRequest) -> Response:
    """
    Delete privileges and role_privilege mappings for a specified module.
    
    This endpoint allows you to:
    - Delete multiple privileges for a module
    - Delete multiple role_privilege mappings for the module
    
    All operations are performed for the specified module_name.
    """
    return await delete_module_service(payload)



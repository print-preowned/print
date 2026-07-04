from fastapi import HTTPException, Response
from app.privilege.model import Privilege, PrivilegeCreateRequest, PrivilegeUpdateRequest
from app.role_privilege.model import RolePrivilegeCreateRequest
from app.module.model import ModuleCreateRequest, ModuleUpdateRequest, ModuleDeleteRequest
from ..privilege.query import (
    create_query as privilege_create_query,
    update_query as privilege_update_query,
    delete_by_code_query as privilege_delete_by_code_query,
    read_by_code_query as privilege_read_by_code_query,
    read_by_id_query as privilege_read_by_id_query,
    read_by_module_name_query as privilege_read_by_module_name_query,
)
from ..role_privilege.query import (
    create_query as role_privilege_create_query,
    read_by_role_and_privilege_query,
    delete_by_role_and_privilege_query,
    read_by_privilege_code_query as role_privilege_read_by_privilege_code_query,
)
from ..role.service import read_owner_role_service
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from app.auth.privilege_catalog import crud_privilege_defs, CrudResourceDef


async def create_module_service(request: ModuleCreateRequest) -> Response:
    """
    Create privileges and role_privilege mappings for a specified module.
    
    This service handles:
    1. Creating all privileges for the module (based on standard privilege patterns)
    2. Creating role_privilege mappings for all privileges to the owner role
    
    All operations are performed for the specified module_name.
    Note: This will create standard CRUD privileges (CREATE, READ, UPDATE, DELETE) for the module.
    """
    module_name = request.module_name
    
    # Get owner role
    owner_role_response = await read_owner_role_service()
    owner_role = owner_role_response.data
    
    if not owner_role:
        raise HTTPException(
            status_code=404,
            detail="Owner role not found. Please ensure standard roles are created."
        )
    
    owner_role_id = owner_role.id

    resource = CrudResourceDef(
        resource=module_name.upper(),
        module=module_name,
        include_delete=module_name.upper() not in {"AUTHOR"},
    )
    privilege_defs = crud_privilege_defs(resource)

    for privilege_def in privilege_defs:
        privilege_code = privilege_def.code

        existing = await privilege_read_by_code_query(privilege_code)
        if existing:
            role_id_str = str(owner_role_id)
            existing_mapping = await read_by_role_and_privilege_query(role_id_str, privilege_code)
            if not existing_mapping:
                mapping = RolePrivilegeCreateRequest(
                    role_id=owner_role_id,
                    privilege_code=privilege_code,
                    status="ACTIVE",
                )
                await role_privilege_create_query(mapping)
            continue

        privilege_data = PrivilegeCreateRequest(
            code=privilege_code,
            name=privilege_def.name,
            module_name=module_name,
            status="ACTIVE",
        )

        await privilege_create_query(privilege_data)

        mapping = RolePrivilegeCreateRequest(
            role_id=owner_role_id,
            privilege_code=privilege_code,
            status="ACTIVE",
        )
        await role_privilege_create_query(mapping)

    return Response(status_code=201)


async def update_module_service(request: ModuleUpdateRequest) -> Response:
    """
    Update all privileges for a specified module and ensure owner role has mappings.
    
    This service handles:
    1. Updating all existing privileges for the module
    2. Ensuring owner role has role_privilege mappings for all privileges
    """
    module_name = request.module_name
    
    # Get owner role
    owner_role_response = await read_owner_role_service()
    owner_role = owner_role_response.data
    
    if not owner_role:
        raise HTTPException(
            status_code=404,
            detail="Owner role not found. Please ensure standard roles are created."
        )
    
    owner_role_id = owner_role.id
    owner_role_id_str = str(owner_role_id)
    
    # Get all privileges for the module
    privileges = await privilege_read_by_module_name_query(module_name)
    
    if not privileges:
        raise HTTPException(
            status_code=404,
            detail=f"No privileges found for module: {module_name}"
        )
    
    # Update all privileges and ensure owner role mappings exist
    for privilege in privileges:
        # Update privilege name to match module name pattern
        update_data = PrivilegeUpdateRequest(
            name=privilege.name,  # Keep existing name or update as needed
            status="ACTIVE"
        )
        
        result = await privilege_update_query(str(privilege.id), update_data)
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to update privilege: {privilege.code}"
            )
        
        # Ensure owner role has mapping for this privilege
        existing_mapping = await read_by_role_and_privilege_query(owner_role_id_str, privilege.code)
        if not existing_mapping:
            # Create role_privilege mapping for owner role
            mapping = RolePrivilegeCreateRequest(
                role_id=owner_role_id,
                privilege_code=privilege.code,
                status="ACTIVE"
            )
            await role_privilege_create_query(mapping)
    
    return Response(status_code=200)


async def delete_module_service(request: ModuleDeleteRequest) -> Response:
    """
    Delete all privileges and role_privilege mappings for a specified module.
    
    This service handles:
    1. Deleting all privileges for the module
    2. Deleting all role_privilege mappings for the module
    """
    module_name = request.module_name
    
    # Get all privileges for the module
    privileges = await privilege_read_by_module_name_query(module_name)
    
    if not privileges:
        raise HTTPException(
            status_code=404,
            detail=f"No privileges found for module: {module_name}"
        )
    
    # Delete all role_privilege mappings for each privilege
    for privilege in privileges:
        privilege_code = privilege.code
        
        # Get all role_privilege mappings for this privilege
        role_privileges = await role_privilege_read_by_privilege_code_query(privilege_code)
        
        # Delete all role_privilege mappings
        for role_priv in role_privileges:
            role_id = str(role_priv.role_id)
            await delete_by_role_and_privilege_query(role_id, privilege_code)
        
        # Delete the privilege
        await privilege_delete_by_code_query(privilege_code)
    
    return Response(status_code=204)



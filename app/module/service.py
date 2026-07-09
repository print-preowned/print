from __future__ import annotations

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.privilege_catalog import CrudResourceDef, crud_privilege_defs
from app.module.model import ModuleCreateRequest, ModuleDeleteRequest, ModuleUpdateRequest
from app.privilege.model import PrivilegeCreateRequest, PrivilegeUpdateRequest
from app.role.service import RoleService
from app.role_privilege.model import RolePrivilegeCreateRequest
from app.utility.model import BaseResponse
from app.utility.service_deps import writable_service

from ..privilege.query import (
    create_query as privilege_create_query,
    delete_by_code_query as privilege_delete_by_code_query,
    read_by_code_query as privilege_read_by_code_query,
    read_by_module_name_query as privilege_read_by_module_name_query,
    update_query as privilege_update_query,
)
from ..role_privilege.query import (
    create_query as role_privilege_create_query,
    delete_by_role_and_privilege_query,
    read_by_privilege_code_query as role_privilege_read_by_privilege_code_query,
    read_by_role_and_privilege_query,
)


class ModuleService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_module(self, request: ModuleCreateRequest) -> Response:
        module_name = request.module_name

        owner_role_response: BaseResponse = await RoleService(self._session).read_owner_role()
        owner_role = owner_role_response.data

        if not owner_role:
            raise HTTPException(
                status_code=404,
                detail="Owner role not found. Please ensure standard roles are created.",
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
                        role_id=str(owner_role_id),
                        privilege_code=privilege_code,
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
                role_id=str(owner_role_id),
                privilege_code=privilege_code,
            )
            await role_privilege_create_query(mapping)

        return Response(status_code=201)

    async def update_module(self, request: ModuleUpdateRequest) -> Response:
        module_name = request.module_name

        owner_role_response: BaseResponse = await RoleService(self._session).read_owner_role()
        owner_role = owner_role_response.data

        if not owner_role:
            raise HTTPException(
                status_code=404,
                detail="Owner role not found. Please ensure standard roles are created.",
            )

        owner_role_id = owner_role.id
        owner_role_id_str = str(owner_role_id)

        privileges = await privilege_read_by_module_name_query(module_name)

        if not privileges:
            raise HTTPException(
                status_code=404,
                detail=f"No privileges found for module: {module_name}",
            )

        for privilege in privileges:
            update_data = PrivilegeUpdateRequest(
                name=privilege.name,
                status="ACTIVE",
            )

            result = await privilege_update_query(str(privilege.id), update_data)
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Failed to update privilege: {privilege.code}",
                )

            existing_mapping = await read_by_role_and_privilege_query(owner_role_id_str, privilege.code)
            if not existing_mapping:
                mapping = RolePrivilegeCreateRequest(
                    role_id=str(owner_role_id),
                    privilege_code=privilege.code,
                )
                await role_privilege_create_query(mapping)

        return Response(status_code=200)

    async def delete_module(self, request: ModuleDeleteRequest) -> Response:
        module_name = request.module_name

        privileges = await privilege_read_by_module_name_query(module_name)

        if not privileges:
            raise HTTPException(
                status_code=404,
                detail=f"No privileges found for module: {module_name}",
            )

        for privilege in privileges:
            privilege_code = privilege.code

            role_privileges = await role_privilege_read_by_privilege_code_query(privilege_code)

            for role_priv in role_privileges:
                role_id = str(role_priv.role_id)
                await delete_by_role_and_privilege_query(role_id, privilege_code)

            await privilege_delete_by_code_query(privilege_code)

        return Response(status_code=204)


class WritableModuleService(writable_service(ModuleService)):
    pass

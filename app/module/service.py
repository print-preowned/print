from __future__ import annotations

import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.privilege_catalog import CrudResourceDef, crud_privilege_defs
from app.module.model import ModuleCreateRequest, ModuleDeleteRequest, ModuleUpdateRequest
from app.privilege.model import PrivilegeCreateRequest, PrivilegeUpdateRequest
from app.privilege.repository import PrivilegeRepository
from app.privilege.schemas import PrivilegeCreate, PrivilegeUpdate
from app.role.service import RoleService
from app.role_privilege.model import RolePrivilegeCreateRequest
from app.role_privilege.repository import RolePrivilegeRepository
from app.role_privilege.schemas import RolePrivilegeCreate
from app.utility.model import BaseResponse
from app.utility.service_deps import writable_service


class ModuleService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._privilege_repo = PrivilegeRepository(session)
        self._role_privilege_repo = RolePrivilegeRepository(session)

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

            existing = await self._privilege_repo.read_privilege_by_code(privilege_code)
            if existing:
                role_id_str = str(owner_role_id)
                existing_mapping = (
                    await self._role_privilege_repo.read_role_privilege_by_role_and_code(
                        uuid.UUID(role_id_str),
                        privilege_code,
                    )
                )
                if not existing_mapping:
                    mapping = RolePrivilegeCreateRequest(
                        role_id=str(owner_role_id),
                        privilege_code=privilege_code,
                    )
                    await self._role_privilege_repo.create_role_privilege(
                        RolePrivilegeCreate(
                            role_id=uuid.UUID(mapping.role_id),
                            privilege_code=mapping.privilege_code,
                        )
                    )
                continue

            privilege_data = PrivilegeCreateRequest(
                code=privilege_code,
                name=privilege_def.name,
                module_name=module_name,
                status="ACTIVE",
            )

            await self._privilege_repo.create_privilege(
                PrivilegeCreate.model_validate(
                    privilege_data.model_dump(include=set(PrivilegeCreate.model_fields.keys()))
                )
            )

            mapping = RolePrivilegeCreateRequest(
                role_id=str(owner_role_id),
                privilege_code=privilege_code,
            )
            await self._role_privilege_repo.create_role_privilege(
                RolePrivilegeCreate(
                    role_id=uuid.UUID(mapping.role_id),
                    privilege_code=mapping.privilege_code,
                )
            )

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

        privileges = await self._privilege_repo.read_privileges_by_module_name(module_name)

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

            updated = await self._privilege_repo.update_privilege(
                privilege.id,
                PrivilegeUpdate.model_validate(update_data.model_dump(exclude_unset=True)),
            )
            if updated is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Failed to update privilege: {privilege.code}",
                )

            existing_mapping = await self._role_privilege_repo.read_role_privilege_by_role_and_code(
                uuid.UUID(owner_role_id_str),
                privilege.code,
            )
            if not existing_mapping:
                mapping = RolePrivilegeCreateRequest(
                    role_id=str(owner_role_id),
                    privilege_code=privilege.code,
                )
                await self._role_privilege_repo.create_role_privilege(
                    RolePrivilegeCreate(
                        role_id=uuid.UUID(mapping.role_id),
                        privilege_code=mapping.privilege_code,
                    )
                )

        return Response(status_code=200)

    async def delete_module(self, request: ModuleDeleteRequest) -> Response:
        module_name = request.module_name

        privileges = await self._privilege_repo.read_privileges_by_module_name(module_name)

        if not privileges:
            raise HTTPException(
                status_code=404,
                detail=f"No privileges found for module: {module_name}",
            )

        for privilege in privileges:
            privilege_code = privilege.code

            role_privileges = await self._role_privilege_repo.read_by_privilege_code(privilege_code)

            for role_priv in role_privileges:
                await self._role_privilege_repo.soft_delete_by_role_and_code(
                    role_priv.role_id,
                    privilege_code,
                )

            await self._privilege_repo.soft_delete_privilege_by_code(privilege_code)

        return Response(status_code=204)


class WritableModuleService(writable_service(ModuleService)):
    pass

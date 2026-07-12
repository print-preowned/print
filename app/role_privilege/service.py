from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.role_privilege.model import RolePrivilegeCreateRequest
from app.role_privilege.repository import RolePrivilegeRepository
from app.role_privilege.schemas import RolePrivilegeCreate, RolePrivilegeRead
from app.business_user.repository import BusinessUserRepository
from app.user.repository import UserRepository
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.revocation import revoke_role_active_sessions
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> RolePrivilegeRead:
    return RolePrivilegeRead.model_validate(row)


class RolePrivilegeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = RolePrivilegeRepository(session)
        self._business_user_repo = BusinessUserRepository(session)
        self._user_repo = UserRepository(session)

    async def create(self, mapping: RolePrivilegeCreateRequest) -> Response:
        payload = RolePrivilegeCreate(
            role_id=_parse_id(mapping.role_id),
            privilege_code=mapping.privilege_code,
        )
        await self._repo.create_role_privilege(payload)
        return Response(status_code=201)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        existing = await self._repo.read_role_privilege_by_id(parsed_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Mapping not found")

        deleted = await self._repo.soft_delete_role_privilege(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Mapping not found")

        await revoke_role_active_sessions(
            self._business_user_repo, self._user_repo, existing.role_id
        )
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[RolePrivilegeRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_role_privileges()
        rows = await self._repo.list_role_privileges(offset=offset, limit=size)
        data = [_to_read(row) for row in rows]

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[RolePrivilegeRead](
            status_code=200,
            message="Successful",
            data=data,
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id(self, id: str) -> BaseResponse[RolePrivilegeRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_role_privilege_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return BaseResponse[RolePrivilegeRead](
            status_code=200,
            message="Successful",
            data=_to_read(row),
        )


class WritableRolePrivilegeService(writable_service(RolePrivilegeService)):
    pass


class ReadableRolePrivilegeService(readable_service(RolePrivilegeService)):
    pass

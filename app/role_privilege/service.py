from __future__ import annotations

import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.role_privilege.model import RolePrivilegeCreateRequest
from app.role_privilege.repository import RolePrivilegeRepository
from app.role_privilege.schemas import RolePrivilegeCreate, RolePrivilegeRead
from app.business_user.repository import BusinessUserRepository
from app.user.repository import UserRepository
from app.utility.model import BaseResponse
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

    async def create(
        self, role_id: str, payload: RolePrivilegeCreateRequest
    ) -> Response:
        parsed_role_id = _parse_id(role_id)
        for privilege_code in payload.privilege_codes:
            existing = await self._repo.read_role_privilege_by_role_and_code(
                parsed_role_id,
                privilege_code,
            )
            if existing is None:
                await self._repo.create_role_privilege(
                    RolePrivilegeCreate(role_id=parsed_role_id, privilege_code=privilege_code)
                )
        return Response(status_code=201)

    async def delete_by_role_and_code(self, role_id: str, privilege_code: str) -> Response:
        parsed_role_id = _parse_id(role_id)
        existing = await self._repo.read_role_privilege_by_role_and_code(
            parsed_role_id,
            privilege_code,
        )
        if existing is None:
            raise HTTPException(status_code=404, detail="Mapping not found")

        deleted = await self._repo.delete_by_role_and_code(parsed_role_id, privilege_code)
        if not deleted:
            raise HTTPException(status_code=404, detail="Mapping not found")

        await revoke_role_active_sessions(
            self._business_user_repo, self._user_repo, parsed_role_id
        )
        return Response(status_code=204)

    async def read_by_role_id(self, role_id: str) -> BaseResponse[list[RolePrivilegeRead]]:
        rows = await self._repo.read_by_role_id(_parse_id(role_id))
        return BaseResponse[list[RolePrivilegeRead]](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
        )

    async def read_by_privilege_code(
        self, privilege_code: str
    ) -> BaseResponse[list[RolePrivilegeRead]]:
        rows = await self._repo.read_by_privilege_code(privilege_code)
        return BaseResponse[list[RolePrivilegeRead]](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
        )


class WritableRolePrivilegeService(writable_service(RolePrivilegeService)):
    pass


class ReadableRolePrivilegeService(readable_service(RolePrivilegeService)):
    pass

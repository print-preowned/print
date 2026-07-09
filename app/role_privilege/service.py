from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.role_privilege.model import RolePrivilegeCreateRequest, RolePrivilegeUpdateRequest
from app.role_privilege.repository import (
    count_role_privileges,
    create_role_privilege,
    list_role_privileges,
    read_role_privilege_by_id,
    soft_delete_role_privilege,
    update_role_privilege,
)
from app.role_privilege.schemas import RolePrivilegeCreate, RolePrivilegeRead, RolePrivilegeUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> RolePrivilegeRead:
    return RolePrivilegeRead.model_validate(row)


class RolePrivilegeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, mapping: RolePrivilegeCreateRequest) -> Response:
        payload = RolePrivilegeCreate(
            role_id=_parse_id(mapping.role_id),
            privilege_code=mapping.privilege_code,
        )
        await create_role_privilege(self._session, payload)
        return Response(status_code=201)

    async def update(self, id: str, mapping: RolePrivilegeUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        update_data = mapping.model_dump(exclude_unset=True)
        if "role_id" in update_data and update_data["role_id"] is not None:
            update_data["role_id"] = _parse_id(update_data["role_id"])

        updated = await update_role_privilege(
            self._session,
            parsed_id,
            RolePrivilegeUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await soft_delete_role_privilege(self._session, parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[RolePrivilegeRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await count_role_privileges(self._session)
        rows = await list_role_privileges(self._session, offset=offset, limit=size)
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
        row = await read_role_privilege_by_id(self._session, parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return BaseResponse[RolePrivilegeRead](
            status_code=200,
            message="Successful",
            data=_to_read(row),
        )


from app.utility.service_deps import readable_service, writable_service

WritableRolePrivilegeService = writable_service(RolePrivilegeService)
ReadableRolePrivilegeService = readable_service(RolePrivilegeService)

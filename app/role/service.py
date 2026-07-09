from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.role.model import OWNER_ROLE_CODE, RoleCreateRequest, RoleUpdateRequest
from app.role.repository import RoleRepository
from app.role.schemas import RoleCreate, RoleRead, RoleUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> RoleRead:
    return RoleRead.model_validate(row)


def _to_create(payload: RoleCreateRequest) -> RoleCreate:
    data = payload.model_dump(include=set(RoleCreate.model_fields.keys()))
    if data.get("code") is None:
        data["code"] = payload.name.upper().replace(" ", "_")
    return RoleCreate.model_validate(data)


class RoleService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = RoleRepository(session)

    async def create(self, role: RoleCreateRequest) -> Response:
        await self._repo.create_role(_to_create(role))
        return Response(status_code=201)

    async def update(self, id: str, role: RoleUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        updated = await self._repo.update_role(
            parsed_id,
            RoleUpdate.model_validate(role.model_dump(exclude_unset=True)),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Role not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await self._repo.soft_delete_role(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Role not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[RoleRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_roles()
        rows = await self._repo.list_roles(offset=offset, limit=size)
        data = [_to_read(row) for row in rows]

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[RoleRead](
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

    async def read_by_id(self, id: str) -> BaseResponse[RoleRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_role_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Role not found")
        return BaseResponse[RoleRead](status_code=200, message="Successful", data=_to_read(row))

    async def read_owner_role(self) -> BaseResponse[RoleRead | None]:
        role = await self._repo.read_role_by_code(OWNER_ROLE_CODE)
        return BaseResponse[RoleRead | None](
            status_code=200,
            message="Successful",
            data=_to_read(role) if role else None,
        )


class WritableRoleService(writable_service(RoleService)):
    pass


class ReadableRoleService(readable_service(RoleService)):
    pass

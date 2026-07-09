from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.privilege.model import PrivilegeCreateRequest, PrivilegeUpdateRequest
from app.privilege.repository import PrivilegeRepository
from app.privilege.schemas import PrivilegeCreate, PrivilegeRead, PrivilegeUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PrivilegeRead:
    return PrivilegeRead.model_validate(row)


def _to_create(payload: PrivilegeCreateRequest) -> PrivilegeCreate:
    return PrivilegeCreate.model_validate(
        payload.model_dump(include=set(PrivilegeCreate.model_fields.keys()))
    )


class PrivilegeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PrivilegeRepository(session)

    async def create(self, privilege: PrivilegeCreateRequest) -> Response:
        await self._repo.create_privilege(_to_create(privilege))
        return Response(status_code=201)

    async def update(self, id: str, privilege: PrivilegeUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        updated = await self._repo.update_privilege(
            parsed_id,
            PrivilegeUpdate.model_validate(privilege.model_dump(exclude_unset=True)),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Privilege not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await self._repo.soft_delete_privilege(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Privilege not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[PrivilegeRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_privileges()
        rows = await self._repo.list_privileges(offset=offset, limit=size)
        data = [_to_read(row) for row in rows]

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[PrivilegeRead](
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

    async def read_by_id(self, id: str) -> BaseResponse[PrivilegeRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_privilege_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Privilege not found")
        return BaseResponse[PrivilegeRead](
            status_code=200, message="Successful", data=_to_read(row)
        )


WritablePrivilegeService = writable_service(PrivilegeService)
ReadablePrivilegeService = readable_service(PrivilegeService)

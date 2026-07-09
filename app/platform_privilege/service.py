from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_privilege.model import (
    PlatformPrivilege,
    PlatformPrivilegeCreateRequest,
    PlatformPrivilegeUpdateRequest,
)
from app.platform_privilege.repository import (
    count_platform_privileges,
    create_platform_privilege,
    list_platform_privileges,
    read_platform_privilege_by_code,
    read_platform_privilege_by_id,
    soft_delete_platform_privilege,
    update_platform_privilege,
)
from app.platform_privilege.schemas import (
    PlatformPrivilegeCreate,
    PlatformPrivilegeRead,
    PlatformPrivilegeUpdate,
)
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest, Pagination
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PlatformPrivilegeRead:
    return PlatformPrivilegeRead.model_validate(row)


def _to_response(row: PlatformPrivilegeRead) -> PlatformPrivilege:
    return PlatformPrivilege.model_validate(row.model_dump(mode="json"))


class PlatformPrivilegeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, platform_privilege: PlatformPrivilegeCreateRequest) -> Response:
        existing = await read_platform_privilege_by_code(self._session, platform_privilege.code)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Platform privilege with code '{platform_privilege.code}' already exists",
            )

        await create_platform_privilege(
            self._session,
            PlatformPrivilegeCreate.model_validate(platform_privilege.model_dump()),
        )
        return Response(status_code=201)

    async def update(self, id: str, platform_privilege: PlatformPrivilegeUpdateRequest) -> Response:
        if platform_privilege.code:
            existing = await read_platform_privilege_by_code(self._session, platform_privilege.code)
            if existing and str(existing.id) != id:
                raise HTTPException(
                    status_code=409,
                    detail=f"Platform privilege with code '{platform_privilege.code}' already exists",
                )

        updated = await update_platform_privilege(
            self._session,
            _parse_id(id),
            PlatformPrivilegeUpdate.model_validate(platform_privilege.model_dump(exclude_unset=True)),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Platform privilege not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        deleted = await soft_delete_platform_privilege(self._session, _parse_id(id))
        if not deleted:
            raise HTTPException(status_code=404, detail="Platform privilege not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[PlatformPrivilege]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await count_platform_privileges(self._session)
        rows = await list_platform_privileges(self._session, offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[PlatformPrivilege](
            status_code=200,
            message="Successful",
            data=[_to_response(_to_read(row)) for row in rows],
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id(self, id: str) -> BaseResponse[PlatformPrivilege]:
        row = await read_platform_privilege_by_id(self._session, _parse_id(id))
        if row is None:
            raise HTTPException(status_code=404, detail="Platform privilege not found")
        return BaseResponse[PlatformPrivilege](
            status_code=200,
            message="Successful",
            data=_to_response(_to_read(row)),
        )

    async def read_by_code(self, code: str) -> BaseResponse[PlatformPrivilege | None]:
        row = await read_platform_privilege_by_code(self._session, code)
        return BaseResponse[PlatformPrivilege | None](
            status_code=200,
            message="Successful",
            data=_to_response(_to_read(row)) if row else None,
        )


class WritablePlatformPrivilegeService(writable_service(PlatformPrivilegeService)):
    pass


class ReadablePlatformPrivilegeService(readable_service(PlatformPrivilegeService)):
    pass

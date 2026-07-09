from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_privilege_set_privilege.model import (
    PlatformPrivilegeSetPrivilege,
    PlatformPrivilegeSetPrivilegeCreateRequest,
    PlatformPrivilegeSetPrivilegeUpdateRequest,
)
from app.platform_privilege_set_privilege.repository import (
    count_platform_privilege_set_privileges,
    create_platform_privilege_set_privilege,
    list_platform_privilege_set_privileges,
    read_by_privilege_set_and_code,
    read_by_privilege_set_id,
    read_platform_privilege_set_privilege_by_id,
    soft_delete_platform_privilege_set_privilege,
    update_platform_privilege_set_privilege,
)
from app.platform_privilege_set_privilege.schemas import (
    PlatformPrivilegeSetPrivilegeCreate,
    PlatformPrivilegeSetPrivilegeRead,
    PlatformPrivilegeSetPrivilegeUpdate,
)
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest, Pagination
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PlatformPrivilegeSetPrivilegeRead:
    return PlatformPrivilegeSetPrivilegeRead.model_validate(row)


def _to_response(row: PlatformPrivilegeSetPrivilegeRead) -> PlatformPrivilegeSetPrivilege:
    return PlatformPrivilegeSetPrivilege.model_validate(row.model_dump(mode="json"))


class PlatformPrivilegeSetPrivilegeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, mapping: PlatformPrivilegeSetPrivilegeCreateRequest) -> Response:
        existing = await read_by_privilege_set_and_code(
            self._session,
            _parse_id(str(mapping.privilege_set_id)),
            mapping.privilege_code,
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="This privilege is already assigned to this privilege set",
            )

        data = mapping.model_dump()
        data["privilege_set_id"] = uuid.UUID(str(data["privilege_set_id"]))
        await create_platform_privilege_set_privilege(
            self._session,
            PlatformPrivilegeSetPrivilegeCreate.model_validate(data),
        )
        return Response(status_code=201)

    async def update(
        self,
        id: str,
        mapping: PlatformPrivilegeSetPrivilegeUpdateRequest,
    ) -> Response:
        updated = await update_platform_privilege_set_privilege(
            self._session,
            _parse_id(id),
            PlatformPrivilegeSetPrivilegeUpdate.model_validate(
                mapping.model_dump(exclude_unset=True)
            ),
        )
        if updated is None:
            raise HTTPException(
                status_code=404,
                detail="Platform privilege set privilege mapping not found",
            )
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        deleted = await soft_delete_platform_privilege_set_privilege(self._session, _parse_id(id))
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Platform privilege set privilege mapping not found",
            )
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[PlatformPrivilegeSetPrivilege]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await count_platform_privilege_set_privileges(self._session)
        rows = await list_platform_privilege_set_privileges(
            self._session,
            offset=offset,
            limit=size,
        )

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[PlatformPrivilegeSetPrivilege](
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

    async def read_by_id(self, id: str) -> BaseResponse[PlatformPrivilegeSetPrivilege]:
        row = await read_platform_privilege_set_privilege_by_id(self._session, _parse_id(id))
        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Platform privilege set privilege mapping not found",
            )
        return BaseResponse[PlatformPrivilegeSetPrivilege](
            status_code=200,
            message="Successful",
            data=_to_response(_to_read(row)),
        )

    async def read_by_privilege_set_id(
        self,
        privilege_set_id: str,
    ) -> BaseResponse[list[PlatformPrivilegeSetPrivilege]]:
        rows = await read_by_privilege_set_id(self._session, _parse_id(privilege_set_id))
        return BaseResponse[list[PlatformPrivilegeSetPrivilege]](
            status_code=200,
            message="Successful",
            data=[_to_response(_to_read(row)) for row in rows],
        )


class WritablePlatformPrivilegeSetPrivilegeService(
    writable_service(PlatformPrivilegeSetPrivilegeService)
):
    pass


class ReadablePlatformPrivilegeSetPrivilegeService(
    readable_service(PlatformPrivilegeSetPrivilegeService)
):
    pass

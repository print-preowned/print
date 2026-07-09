from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_privilege_set.model import (
    PlatformPrivilegeSet,
    PlatformPrivilegeSetCreateRequest,
    PlatformPrivilegeSetUpdateRequest,
)
from app.platform_privilege_set.repository import (
    count_platform_privilege_sets,
    create_platform_privilege_set,
    list_platform_privilege_sets,
    read_platform_privilege_set_by_id,
    soft_delete_platform_privilege_set,
    update_platform_privilege_set,
)
from app.platform_privilege_set.schemas import (
    PlatformPrivilegeSetCreate,
    PlatformPrivilegeSetRead,
    PlatformPrivilegeSetUpdate,
)
from app.platform_user.guards import SUPER_ADMIN_SET_NAME
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest, Pagination
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PlatformPrivilegeSetRead:
    return PlatformPrivilegeSetRead.model_validate(row)


def _to_response(row: PlatformPrivilegeSetRead) -> PlatformPrivilegeSet:
    return PlatformPrivilegeSet.model_validate(row.model_dump(mode="json"))


class PlatformPrivilegeSetService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, platform_privilege_set: PlatformPrivilegeSetCreateRequest) -> Response:
        await create_platform_privilege_set(
            self._session,
            PlatformPrivilegeSetCreate.model_validate(platform_privilege_set.model_dump()),
        )
        return Response(status_code=201)

    async def update(
        self,
        id: str,
        platform_privilege_set: PlatformPrivilegeSetUpdateRequest,
    ) -> Response:
        updated = await update_platform_privilege_set(
            self._session,
            _parse_id(id),
            PlatformPrivilegeSetUpdate.model_validate(
                platform_privilege_set.model_dump(exclude_unset=True)
            ),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Platform privilege set not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        deleted = await soft_delete_platform_privilege_set(self._session, _parse_id(id))
        if not deleted:
            raise HTTPException(status_code=404, detail="Platform privilege set not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[PlatformPrivilegeSet]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size
        exclude_names = [SUPER_ADMIN_SET_NAME]

        total_results = await count_platform_privilege_sets(
            self._session,
            exclude_names=exclude_names,
        )
        rows = await list_platform_privilege_sets(
            self._session,
            offset=offset,
            limit=size,
            exclude_names=exclude_names,
        )

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[PlatformPrivilegeSet](
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

    async def read_by_id(self, id: str) -> BaseResponse[PlatformPrivilegeSet]:
        row = await read_platform_privilege_set_by_id(self._session, _parse_id(id))
        if row is None:
            raise HTTPException(status_code=404, detail="Platform privilege set not found")
        return BaseResponse[PlatformPrivilegeSet](
            status_code=200,
            message="Successful",
            data=_to_response(_to_read(row)),
        )


class WritablePlatformPrivilegeSetService(writable_service(PlatformPrivilegeSetService)):
    pass


class ReadablePlatformPrivilegeSetService(readable_service(PlatformPrivilegeSetService)):
    pass

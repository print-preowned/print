from fastapi import HTTPException, Response
from app.platform_privilege_set.model import (
    PlatformPrivilegeSet,
    PlatformPrivilegeSetCreateRequest,
    PlatformPrivilegeSetUpdateRequest,
)
from app.platform_user.guards import SUPER_ADMIN_SET_NAME
from .query import (
    delete_query,
    read_query,
    read_by_id_query,
    create_query,
    update_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(platform_privilege_set: PlatformPrivilegeSetCreateRequest) -> Response:
    await create_query(platform_privilege_set)
    return Response(status_code=201)


async def update_service(id: str, platform_privilege_set: PlatformPrivilegeSetUpdateRequest) -> Response:
    update = await update_query(id, platform_privilege_set)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Platform privilege set not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Platform privilege set not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[PlatformPrivilegeSet]:
    platform_privilege_sets = await read_query(
        params,
        exclude_names=[SUPER_ADMIN_SET_NAME],
    )
    return PaginatedResponse[PlatformPrivilegeSet](
        status_code=200,
        message="Successful",
        data=platform_privilege_sets.data,
        pagination=platform_privilege_sets.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[PlatformPrivilegeSet]:
    platform_privilege_set = await read_by_id_query(id)
    if platform_privilege_set is None:
        raise HTTPException(status_code=404, detail="Platform privilege set not found")
    return BaseResponse[PlatformPrivilegeSet](status_code=200, message="Successful", data=platform_privilege_set)

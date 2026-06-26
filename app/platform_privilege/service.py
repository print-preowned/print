from fastapi import HTTPException, Response
from app.platform_privilege.model import PlatformPrivilege, PlatformPrivilegeCreateRequest, PlatformPrivilegeUpdateRequest
from .query import (
    delete_query,
    read_query,
    read_by_id_query,
    read_by_code_query,
    create_query,
    update_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(platform_privilege: PlatformPrivilegeCreateRequest) -> Response:
    # Check if privilege with same code already exists
    existing = await read_by_code_query(platform_privilege.code)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Platform privilege with code '{platform_privilege.code}' already exists"
        )
    
    await create_query(platform_privilege)
    return Response(status_code=201)


async def update_service(id: str, platform_privilege: PlatformPrivilegeUpdateRequest) -> Response:
    # If code is being updated, check for duplicates
    if platform_privilege.code:
        existing = await read_by_code_query(platform_privilege.code)
        if existing and str(existing.id) != id:
            raise HTTPException(
                status_code=409,
                detail=f"Platform privilege with code '{platform_privilege.code}' already exists"
            )
    
    update = await update_query(id, platform_privilege)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Platform privilege not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Platform privilege not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[PlatformPrivilege]:
    platform_privileges = await read_query(params)
    return PaginatedResponse[PlatformPrivilege](
        status_code=200,
        message="Successful",
        data=platform_privileges.data,
        pagination=platform_privileges.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[PlatformPrivilege]:
    platform_privilege = await read_by_id_query(id)
    if platform_privilege is None:
        raise HTTPException(status_code=404, detail="Platform privilege not found")
    return BaseResponse[PlatformPrivilege](status_code=200, message="Successful", data=platform_privilege)


async def read_by_code_service(code: str) -> BaseResponse[PlatformPrivilege | None]:
    platform_privilege = await read_by_code_query(code)
    return BaseResponse[PlatformPrivilege | None](status_code=200, message="Successful", data=platform_privilege)

from fastapi import HTTPException, Response
from app.platform_privilege_set_privilege.model import PlatformPrivilegeSetPrivilege, PlatformPrivilegeSetPrivilegeCreateRequest, PlatformPrivilegeSetPrivilegeUpdateRequest
from .query import (
    delete_query,
    read_query,
    read_by_id_query,
    read_by_privilege_set_id_query,
    read_by_privilege_set_and_privilege_query,
    delete_by_privilege_set_and_privilege_query,
    create_query,
    update_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(mapping: PlatformPrivilegeSetPrivilegeCreateRequest) -> Response:
    # Check if mapping already exists
    existing = await read_by_privilege_set_and_privilege_query(
        str(mapping.privilege_set_id),
        mapping.privilege_code
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="This privilege is already assigned to this privilege set"
        )
    
    await create_query(mapping)
    return Response(status_code=201)


async def update_service(id: str, mapping: PlatformPrivilegeSetPrivilegeUpdateRequest) -> Response:
    update = await update_query(id, mapping)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Platform privilege set privilege mapping not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Platform privilege set privilege mapping not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[PlatformPrivilegeSetPrivilege]:
    mappings = await read_query(params)
    return PaginatedResponse[PlatformPrivilegeSetPrivilege](
        status_code=200,
        message="Successful",
        data=mappings.data,
        pagination=mappings.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[PlatformPrivilegeSetPrivilege]:
    mapping = await read_by_id_query(id)
    if mapping is None:
        raise HTTPException(status_code=404, detail="Platform privilege set privilege mapping not found")
    return BaseResponse[PlatformPrivilegeSetPrivilege](status_code=200, message="Successful", data=mapping)


async def read_by_privilege_set_id_service(privilege_set_id: str) -> BaseResponse[list[PlatformPrivilegeSetPrivilege]]:
    mappings = await read_by_privilege_set_id_query(privilege_set_id)
    return BaseResponse[list[PlatformPrivilegeSetPrivilege]](
        status_code=200,
        message="Successful",
        data=mappings
    )

from fastapi import HTTPException, Response
from app.role_privilege.model import (
    RolePrivilege,
    RolePrivilegeCreateRequest,
    RolePrivilegeUpdateRequest,
)
from .query import delete_query, read_query, read_by_id_query, create_query, update_query
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(mapping: RolePrivilegeCreateRequest) -> Response:
    await create_query(mapping)
    return Response(status_code=201)


async def update_service(id: str, mapping: RolePrivilegeUpdateRequest) -> Response:
    update = await update_query(id, mapping)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[RolePrivilege]:
    mappings = await read_query(params)
    return PaginatedResponse[RolePrivilege](
        status_code=200,
        message="Successful",
        data=mappings.data,
        pagination=mappings.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[RolePrivilege]:
    mapping = await read_by_id_query(id)
    if mapping is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return BaseResponse[RolePrivilege](status_code=200, message="Successful", data=mapping)



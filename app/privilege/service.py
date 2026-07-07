from fastapi import HTTPException, Response
from app.privilege.model import PrivilegeCreateRequest, PrivilegeUpdateRequest
from app.privilege.schemas import PrivilegeRead
from .query import delete_query, read_query, read_by_id_query, create_query, update_query
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(privilege: PrivilegeCreateRequest) -> Response:
    await create_query(privilege)
    return Response(status_code=201)


async def update_service(id: str, privilege: PrivilegeUpdateRequest) -> Response:
    update = await update_query(id, privilege)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Privilege not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Privilege not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[PrivilegeRead]:
    privileges = await read_query(params)
    return PaginatedResponse[PrivilegeRead](
        status_code=200,
        message="Successful",
        data=privileges.data,
        pagination=privileges.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[PrivilegeRead]:
    privilege = await read_by_id_query(id)
    if privilege is None:
        raise HTTPException(status_code=404, detail="Privilege not found")
    return BaseResponse[PrivilegeRead](status_code=200, message="Successful", data=privilege)



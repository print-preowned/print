from fastapi import HTTPException, Response
from app.role.model import Role, RoleCreateRequest, RoleUpdateRequest, OWNER_ROLE_CODE
from .query import delete_query, read_query, read_by_id_query, create_query, update_query, read_by_code_query
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(role: RoleCreateRequest) -> Response:
    await create_query(role)
    return Response(status_code=201)


async def update_service(id: str, role: RoleUpdateRequest) -> Response:
    update = await update_query(id, role)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Role not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Role not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[Role]:
    roles = await read_query(params)
    return PaginatedResponse[Role](
        status_code=200,
        message="Successful",
        data=roles.data,
        pagination=roles.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[Role]:
    role = await read_by_id_query(id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return BaseResponse[Role](status_code=200, message="Successful", data=role)


async def read_owner_role_service() -> BaseResponse[Role | None]:
    """
    Get the Owner role by code.
    Returns the Owner role if found, None otherwise.
    """
    role = await read_by_code_query(OWNER_ROLE_CODE)
    return BaseResponse[Role | None](status_code=200, message="Successful", data=role)



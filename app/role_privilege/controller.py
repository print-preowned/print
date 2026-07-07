from app.role_privilege.model import RolePrivilegeCreateRequest, RolePrivilegeUpdateRequest
from app.role_privilege.schemas import RolePrivilegeRead
from .service import (
    delete_service,
    read_service,
    read_by_id_service,
    create_service,
    update_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from fastapi import APIRouter, Response

router = APIRouter(prefix="/role-privilege", tags=["RolePrivilegeController"])


@router.post("/create")
async def create(payload: RolePrivilegeCreateRequest) -> Response:
    return await create_service(payload)


@router.put("/update/{id}")
async def update(id: str, payload: RolePrivilegeUpdateRequest) -> Response:
    return await update_service(id, payload)


@router.delete("/delete/{id}")
async def delete(id) -> Response:
    return await delete_service(id)


@router.get("/read")
async def read(
    page: int = 1, size: int = 5, search: str | None = None
) -> PaginatedResponse[RolePrivilegeRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}")
async def read_by_id(id: str) -> BaseResponse[RolePrivilegeRead]:
    return await read_by_id_service(id)



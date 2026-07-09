from fastapi import APIRouter, Depends, Response

from app.role_privilege.model import RolePrivilegeCreateRequest, RolePrivilegeUpdateRequest
from app.role_privilege.schemas import RolePrivilegeRead
from app.role_privilege.service import ReadableRolePrivilegeService, WritableRolePrivilegeService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/role-privilege", tags=["RolePrivilegeController"])


@router.post("/create")
async def create(
    payload: RolePrivilegeCreateRequest,
    service: WritableRolePrivilegeService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: RolePrivilegeUpdateRequest,
    service: WritableRolePrivilegeService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableRolePrivilegeService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableRolePrivilegeService = Depends(),
) -> PaginatedResponse[RolePrivilegeRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableRolePrivilegeService = Depends(),
) -> BaseResponse[RolePrivilegeRead]:
    return await service.read_by_id(id)

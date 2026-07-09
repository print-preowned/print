from fastapi import APIRouter, Depends, Response

from app.role.model import RoleCreateRequest, RoleUpdateRequest
from app.role.schemas import RoleRead
from app.role.service import ReadableRoleService, WritableRoleService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/role", tags=["RoleController"])


@router.post("/create")
async def create(
    payload: RoleCreateRequest,
    service: WritableRoleService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: RoleUpdateRequest,
    service: WritableRoleService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableRoleService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableRoleService = Depends(),
) -> PaginatedResponse[RoleRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableRoleService = Depends(),
) -> BaseResponse[RoleRead]:
    return await service.read_by_id(id)

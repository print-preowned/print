from fastapi import APIRouter, Depends, Response

from app.role_privilege.model import RolePrivilegeCreateRequest, RolePrivilegeUpdateRequest
from app.role_privilege.schemas import RolePrivilegeRead
from app.role_privilege.service import ReadableRolePrivilegeService, WritableRolePrivilegeService
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/roles/{role_id}/privileges", tags=["role-privileges"])


@router.post("", status_code=201)
async def create(
    role_id: str,
    payload: RolePrivilegeCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_ROLE_PRIVILEGE")),
    service: WritableRolePrivilegeService = Depends(),
) -> Response:
    return await service.create(payload)


@router.patch("/{id}")
async def update(
    role_id: str,
    id: str,
    payload: RolePrivilegeUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_ROLE_PRIVILEGE")),
    service: WritableRolePrivilegeService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/{id}")
async def delete(
    role_id: str,
    id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_ROLE_PRIVILEGE")),
    service: WritableRolePrivilegeService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("")
async def read(
    role_id: str,
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_ROLE_PRIVILEGE")),
    service: ReadableRolePrivilegeService = Depends(),
) -> PaginatedResponse[RolePrivilegeRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/{id}")
async def read_by_id(
    role_id: str,
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_ROLE_PRIVILEGE")),
    service: ReadableRolePrivilegeService = Depends(),
) -> BaseResponse[RolePrivilegeRead]:
    return await service.read_by_id(id)

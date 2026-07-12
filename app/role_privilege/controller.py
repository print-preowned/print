from fastapi import APIRouter, Depends, Response

from app.role_privilege.model import RolePrivilegeCreateRequest
from app.role_privilege.schemas import RolePrivilegeRead
from app.role_privilege.service import ReadableRolePrivilegeService, WritableRolePrivilegeService
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse

router = APIRouter(prefix="/roles/{role_id}/privileges", tags=["role-privileges"])
privilege_router = APIRouter(prefix="/privileges/{privilege_code}/roles", tags=["role-privileges"])


@router.post("", status_code=201)
async def create(
    role_id: str,
    payload: RolePrivilegeCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_ROLE_PRIVILEGE")),
    service: WritableRolePrivilegeService = Depends(),
) -> Response:
    return await service.create(role_id, payload)


@router.delete("/{privilege_code}")
async def delete_by_role_and_privilege(
    role_id: str,
    privilege_code: str,
    token: TokenPayload = Depends(require_privilege("DELETE_ROLE_PRIVILEGE")),
    service: WritableRolePrivilegeService = Depends(),
) -> Response:
    return await service.delete_by_role_and_code(role_id, privilege_code)


@router.get("")
async def read_by_role_id(
    role_id: str,
    token: TokenPayload = Depends(require_privilege("READ_ROLE_PRIVILEGE")),
    service: ReadableRolePrivilegeService = Depends(),
) -> BaseResponse[list[RolePrivilegeRead]]:
    return await service.read_by_role_id(role_id)


@privilege_router.get("")
async def read_by_privilege_code(
    privilege_code: str,
    token: TokenPayload = Depends(require_privilege("READ_ROLE_PRIVILEGE")),
    service: ReadableRolePrivilegeService = Depends(),
) -> BaseResponse[list[RolePrivilegeRead]]:
    return await service.read_by_privilege_code(privilege_code)

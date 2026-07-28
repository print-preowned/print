from fastapi import APIRouter, Depends, Response

from app.role.model import RoleCreateRequest, RoleUpdateRequest
from app.role.schemas import RoleRead
from app.role.service import ReadableRoleService, WritableRoleService
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, pagination_params_with

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("", status_code=201)
async def create(
    payload: RoleCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_ROLE")),
    service: WritableRoleService = Depends(),
) -> BaseResponse[RoleRead]:
    return await service.create(payload)


@router.patch("/{id}")
async def update(
    id: str,
    payload: RoleUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_ROLE")),
    service: WritableRoleService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/{id}")
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_ROLE")),
    service: WritableRoleService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("")
async def read(
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    token: TokenPayload = Depends(require_privilege("READ_ROLE")),
    service: ReadableRoleService = Depends(),
) -> PaginatedResponse[RoleRead]:
    return await service.read(params)


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_ROLE")),
    service: ReadableRoleService = Depends(),
) -> BaseResponse[RoleRead]:
    return await service.read_by_id(id)

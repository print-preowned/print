from fastapi import APIRouter, Depends, Response

from app.privilege.model import PrivilegeCreateRequest, PrivilegeUpdateRequest
from app.privilege.schemas import PrivilegeRead
from app.privilege.service import ReadablePrivilegeService, WritablePrivilegeService
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/privileges", tags=["privileges"])


@router.post("", status_code=201)
async def create(
    payload: PrivilegeCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_PRIVILEGE")),
    service: WritablePrivilegeService = Depends(),
) -> Response:
    return await service.create(payload)


@router.patch("/{id}")
async def update(
    id: str,
    payload: PrivilegeUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_PRIVILEGE")),
    service: WritablePrivilegeService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/{id}")
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_PRIVILEGE")),
    service: WritablePrivilegeService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    token: TokenPayload = Depends(require_privilege("READ_PRIVILEGE")),
    service: ReadablePrivilegeService = Depends(),
) -> PaginatedResponse[PrivilegeRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_PRIVILEGE")),
    service: ReadablePrivilegeService = Depends(),
) -> BaseResponse[PrivilegeRead]:
    return await service.read_by_id(id)

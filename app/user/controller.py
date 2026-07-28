from fastapi import APIRouter, Depends, Response

from app.user.model import UserUpdateRequest
from app.user.schemas import UserRead
from app.user.service import ReadableUserService, WritableUserService
from app.utility.model import BaseResponse, PaginatedResponse
from app.utility.pagination import PaginationParams, pagination_params_with

router = APIRouter(prefix="/users", tags=["UserController"])


@router.put("/{id}")
async def update(
    id: str,
    payload: UserUpdateRequest,
    service: WritableUserService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/{id}")
async def delete(
    id: str,
    service: WritableUserService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("")
async def read(
    params: PaginationParams = Depends(pagination_params_with(default_size=5)),
    service: ReadableUserService = Depends(),
) -> PaginatedResponse[UserRead]:
    return await service.read(params)


@router.get("/by-role/{role_id}")
async def read_by_role(
    role_id: str,
    service: ReadableUserService = Depends(),
) -> BaseResponse[list[UserRead]]:
    return await service.read_by_role_id(role_id)


@router.get("/{id}")
async def read_by_id(
    id: str,
    service: ReadableUserService = Depends(),
) -> BaseResponse[UserRead]:
    return await service.read_by_id(id)

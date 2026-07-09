from fastapi import APIRouter, Depends, Request, Response

from app.user.model import (
    ContextSwitchRequest,
    ContextSwitchResponse,
    LoginRequest,
    LoginResponse,
    SignupRequest,
    UserUpdateRequest,
)
from app.user.schemas import UserRead
from app.user.service import ReadableUserService, WritableUserService
from app.utility.authorization import TokenPayload, get_token_payload
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/user", tags=["UserController"])


@router.post("/signup")
async def signup(
    request: Request,
    payload: SignupRequest,
    service: WritableUserService = Depends(),
) -> LoginResponse:
    return await service.signup(request, payload)


@router.post("/login")
async def login(
    request: Request,
    payload: LoginRequest,
    service: ReadableUserService = Depends(),
) -> LoginResponse:
    return await service.login(request, payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: UserUpdateRequest,
    service: WritableUserService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableUserService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableUserService = Depends(),
) -> PaginatedResponse[UserRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableUserService = Depends(),
) -> BaseResponse[UserRead]:
    return await service.read_by_id(id)


@router.get("/read/by-role/{role_id}")
async def read_by_role(
    role_id: str,
    service: ReadableUserService = Depends(),
) -> BaseResponse[list[UserRead]]:
    return await service.read_by_role_id(role_id)


@router.post("/context/switch")
async def switch_context(
    payload: ContextSwitchRequest,
    token: TokenPayload = Depends(get_token_payload),
    service: ReadableUserService = Depends(),
) -> ContextSwitchResponse:
    """
    Switch context between CUSTOMER and BUSINESS

    Following MDC-CONTEXT-3: token_reissue_on_context_switch
    - Validates that current context is not the same as target context
    - Returns a new token for the target context
    """
    return await service.switch_context(token, payload.target_context)

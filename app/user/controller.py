from app.user.model import (
    ContextSwitchRequest,
    ContextSwitchResponse,
    LoginRequest,
    LoginResponse,
    SignupRequest,
    UserUpdateRequest,
)
from app.user.schemas import UserRead
from .service import (
    delete_service,
    read_service,
    read_by_id_service,
    signup_service,
    update_service,
    read_by_role_id_service,
    login_service,
    switch_context_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest, PyObjectId
from ..utility.authorization import get_token_payload, TokenPayload
from fastapi import APIRouter, Request, Response, Depends

router = APIRouter(prefix="/user", tags=["UserController"])


@router.post("/signup")
async def signup(request: Request, payload: SignupRequest) -> LoginResponse:
    return await signup_service(request, payload)


@router.post("/login")
async def login(request: Request, payload: LoginRequest):
    return await login_service(request, payload)


@router.put("/update/{id}")
async def update(id: str, payload: UserUpdateRequest) -> Response:
    return await update_service(id, payload)


@router.delete("/delete/{id}")
async def delete(id) -> Response:
    return await delete_service(id)


@router.get("/read")
async def read(
    page: int = 1, size: int = 5, search: str | None = None
) -> PaginatedResponse[UserRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}")
async def read_by_id(id: str) -> BaseResponse[UserRead]:
    return await read_by_id_service(id)


@router.get("/read/by-role/{role_id}")
async def read_by_role(role_id: str) -> BaseResponse[list[UserRead]]:
    return await read_by_role_id_service(role_id)


@router.post("/context/switch")
async def switch_context(
    request: Request,
    payload: ContextSwitchRequest,
    token: TokenPayload = Depends(get_token_payload)
) -> ContextSwitchResponse:
    """
    Switch context between CUSTOMER and BUSINESS
    
    Following MDC-CONTEXT-3: token_reissue_on_context_switch
    - Validates that current context is not the same as target context
    - Returns a new token for the target context
    """
    return await switch_context_service(token, payload.target_context)



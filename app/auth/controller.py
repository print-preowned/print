from fastapi import APIRouter, Depends, Request

from app.user.model import ContextSwitchResponse, LoginRequest, LoginResponse, SignupRequest
from app.user.service import ReadableUserService, WritableUserService
from app.utility.authorization import TokenPayload, get_token_payload

router = APIRouter(prefix="/auth", tags=["AuthController"])


@router.post("/signup", status_code=200)
async def signup(
    request: Request,
    payload: SignupRequest,
    service: WritableUserService = Depends(),
) -> LoginResponse:
    return await service.signup(request, payload)


@router.post("/login", status_code=200)
async def login(
    request: Request,
    payload: LoginRequest,
    service: ReadableUserService = Depends(),
) -> LoginResponse:
    return await service.login(request, payload)


@router.post("/context/business/{business_id}", status_code=200)
async def switch_to_business(
    business_id: str,
    token: TokenPayload = Depends(get_token_payload),
    service: ReadableUserService = Depends(),
) -> ContextSwitchResponse:
    """
    Switch to BUSINESS context for the given business.

    Following MDC-CONTEXT-3: token_reissue_on_context_switch
    """
    return await service.switch_to_business(token, business_id)


@router.post("/context/customer", status_code=200)
async def switch_to_customer(
    token: TokenPayload = Depends(get_token_payload),
    service: ReadableUserService = Depends(),
) -> ContextSwitchResponse:
    """
    Switch to CUSTOMER context.

    Following MDC-CONTEXT-3: token_reissue_on_context_switch
    """
    return await service.switch_to_customer(token)

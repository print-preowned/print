from fastapi import APIRouter, Depends, Request, Response
from app.platform_user.model import (
    PlatformUser,
    PlatformUserCreateRequest,
    PlatformUserUpdateRequest,
    PlatformUserWithUser,
    SuperAdminTransferRequest,
)
from app.platform_user.service import (
    create_service,
    login_service,
    update_service,
    delete_service,
    read_service,
    read_by_id_service,
    read_by_user_id_service,
    read_me_service,
    transfer_super_admin_service,
)
from app.user.model import LoginRequest, LoginResponse
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest
from app.utility.authorization import TokenPayload, require_context, require_privilege

router = APIRouter(prefix="/platform-user", tags=["platform-user"])


# Removed direct signup endpoint - platform users must be created via invite acceptance
# Following MDC-PU-S-1: no_user_created_before_invite_acceptance
# Use /platform-invite/accept endpoint instead
    

@router.post("", status_code=201, tags=["platform"])
async def create(
    platform_user: PlatformUserCreateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS"))
) -> Response:
    """
    Create a platform user
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await create_service(platform_user)

@router.post("/login", status_code=200, tags=["platform"])
async def login(request: Request, payload: LoginRequest) -> LoginResponse:
    return await login_service(request, payload)


@router.get("/me", status_code=200, tags=["platform"])
async def read_me(
    token: TokenPayload = Depends(require_context("PLATFORM")),
) -> BaseResponse[PlatformUserWithUser]:
    """Read the signed-in platform user's record."""
    return await read_me_service(token.sub)


@router.post("/transfer-super-admin", status_code=200, tags=["platform"])
async def transfer_super_admin(
    body: SuperAdminTransferRequest,
    token: TokenPayload = Depends(require_context("PLATFORM")),
) -> Response:
    """Transfer super admin role to another platform user. Caller must be the current super admin."""
    return await transfer_super_admin_service(
        token.sub,
        str(body.target_platform_user_id),
    )


@router.put("/{id}", status_code=200, tags=["platform"])
async def update(
    id: str,
    platform_user: PlatformUserUpdateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS"))
) -> Response:
    """
    Update a platform user
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await update_service(id, platform_user)


@router.delete("/{id}", status_code=204, tags=["platform"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS"))
) -> Response:
    """
    Delete a platform user
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await delete_service(id)


@router.get("", status_code=200, tags=["platform"])
async def read(
    params: ParamRequest = Depends(),
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS"))
) -> PaginatedResponse[PlatformUserWithUser]:
    """
    Read platform users (paginated) with user email and name populated.
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege.
    """
    return await read_service(params)


@router.get("/{id}", status_code=200, tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS"))
) -> BaseResponse[PlatformUser]:
    """
    Read a platform user by ID
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await read_by_id_service(id)


@router.get("/user/{user_id}", status_code=200, tags=["platform"])
async def read_by_user_id(
    user_id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS"))
) -> BaseResponse[PlatformUser | None]:
    """
    Read a platform user by user ID
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await read_by_user_id_service(user_id)

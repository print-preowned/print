from fastapi import APIRouter, Depends, Request, Response

from app.platform_user.model import (
    PlatformUser,
    PlatformUserCreateRequest,
    PlatformUserUpdateRequest,
    PlatformUserWithUser,
    SuperAdminTransferRequest,
)
from app.platform_user.service import ReadablePlatformUserService, WritablePlatformUserService
from app.user.model import LoginRequest, LoginResponse
from app.utility.authorization import TokenPayload, require_context, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/platform-user", tags=["platform-user"])


@router.post("", status_code=201, tags=["platform"])
async def create(
    platform_user: PlatformUserCreateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: WritablePlatformUserService = Depends(),
) -> Response:
    """
    Create a platform user
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await service.create(platform_user)


@router.post("/login", status_code=200, tags=["platform"])
async def login(
    request: Request,
    payload: LoginRequest,
    service: ReadablePlatformUserService = Depends(),
) -> LoginResponse:
    return await service.login(request, payload)


@router.get("/me", status_code=200, tags=["platform"])
async def read_me(
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: ReadablePlatformUserService = Depends(),
) -> BaseResponse[PlatformUserWithUser]:
    """Read the signed-in platform user's record."""
    return await service.read_me(token.sub)


@router.post("/transfer-super-admin", status_code=200, tags=["platform"])
async def transfer_super_admin(
    body: SuperAdminTransferRequest,
    token: TokenPayload = Depends(require_context("PLATFORM")),
    service: WritablePlatformUserService = Depends(),
) -> Response:
    """Transfer super admin role. Caller must be the current super admin."""
    return await service.transfer_super_admin(
        token.sub,
        str(body.target_platform_user_id),
    )


@router.put("/{id}", status_code=200, tags=["platform"])
async def update(
    id: str,
    platform_user: PlatformUserUpdateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: WritablePlatformUserService = Depends(),
) -> Response:
    """
    Update a platform user
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await service.update(id, platform_user)


@router.delete("/{id}", status_code=204, tags=["platform"])
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: WritablePlatformUserService = Depends(),
) -> Response:
    """
    Delete a platform user
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await service.delete(id)


@router.get("", status_code=200, tags=["platform"])
async def read(
    params: ParamRequest = Depends(),
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: ReadablePlatformUserService = Depends(),
) -> PaginatedResponse[PlatformUserWithUser]:
    """
    Read platform users (paginated) with user email and name populated.
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege.
    """
    return await service.read(params)


@router.get("/{id}", status_code=200, tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: ReadablePlatformUserService = Depends(),
) -> BaseResponse[PlatformUser]:
    """
    Read a platform user by ID
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await service.read_by_id(id)


@router.get("/user/{user_id}", status_code=200, tags=["platform"])
async def read_by_user_id(
    user_id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: ReadablePlatformUserService = Depends(),
) -> BaseResponse[PlatformUser | None]:
    """
    Read a platform user by user ID
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await service.read_by_user_id(user_id)

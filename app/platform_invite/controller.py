from fastapi import APIRouter, Depends, Response

from app.platform_invite.model import (
    PlatformInvite,
    PlatformInviteAcceptRequest,
    PlatformInviteCreateRequest,
    PlatformInviteRejectRequest,
    PlatformInviteResendRequest,
    PlatformInviteValidateResponse,
    PlatformInviteWithPrivilegeSet,
)
from app.platform_invite.service import ReadablePlatformInviteService, WritablePlatformInviteService
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/platform-invite", tags=["platform-invite"])


@router.post("/create", status_code=201, tags=["platform"])
async def create(
    invite: PlatformInviteCreateRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: WritablePlatformInviteService = Depends(),
) -> dict:
    """
    Create a platform invite

    Following MDC-PU invite_creation:
    - Admin creates invite with email and privilege_set_id
    - System generates random token
    - Stores hash in PLATFORM_INVITE
    - Returns invite metadata (token is sent via email only)
    - Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await service.create_invite(invite, token.sub)


@router.patch("/{id}/resend", status_code=200, tags=["platform"])
async def resend(
    id: str,
    body: PlatformInviteResendRequest,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: WritablePlatformInviteService = Depends(),
) -> dict:
    """
    Resend a pending invite with a new token.
    Optionally update privilege set and reset expiry from server default.
    Invalidates previous links.
    """
    return await service.resend_invite(id, body, token.sub)


@router.post("/{id}/revoke", status_code=200, tags=["platform"])
async def revoke(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: WritablePlatformInviteService = Depends(),
) -> Response:
    """Revoke a pending invite (admin). Invalidates the token without emailing the invitee."""
    return await service.revoke_invite(id)


@router.get("/validate", status_code=200, tags=["platform"])
async def validate(
    token: str,
    service: ReadablePlatformInviteService = Depends(),
) -> PlatformInviteValidateResponse:
    """
    Validate an invite token (public endpoint)

    Following MDC-PU invite_validation:
    - Hash token
    - Find pending invite by hash
    - Ensure not expired
    - Public endpoint (no auth required)
    """
    return await service.validate_invite(token)


@router.post("/accept", status_code=201)
async def accept(
    accept_request: PlatformInviteAcceptRequest,
    service: WritablePlatformInviteService = Depends(),
) -> Response:
    """
    Accept a platform invite (public endpoint)

    Following MDC-PU invite_acceptance:
    - Validates invite
    - Creates USER
    - Creates PLATFORM_USER
    - Marks invite accepted
    - Public endpoint (no auth required)
    """
    return await service.accept_invite(accept_request)


@router.post("/reject", status_code=200)
async def reject(
    reject_request: PlatformInviteRejectRequest,
    service: WritablePlatformInviteService = Depends(),
) -> Response:
    """
    Reject a platform invite (public endpoint)

    Following MDC-PU invite_rejection:
    - Marks invite rejected
    - Public endpoint (no auth required)
    """
    return await service.reject_invite(reject_request)


@router.get("", status_code=200, tags=["platform"])
async def read(
    params: ParamRequest = Depends(),
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: ReadablePlatformInviteService = Depends(),
) -> PaginatedResponse[PlatformInviteWithPrivilegeSet]:
    """
    Read platform invites (paginated)
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await service.read(params)


@router.get("/{id}", status_code=200, tags=["platform"])
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("MANAGE_PLATFORM_USERS")),
    service: ReadablePlatformInviteService = Depends(),
) -> BaseResponse[PlatformInvite]:
    """
    Read a platform invite by ID
    Requires PLATFORM context and MANAGE_PLATFORM_USERS privilege
    """
    return await service.read_by_id(id)

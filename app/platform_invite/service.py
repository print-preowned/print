from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Response
from app.platform_invite.model import (
    PlatformInvite,
    PlatformInviteCreateRequest,
    PlatformInviteValidateResponse,
    PlatformInviteAcceptRequest,
    PlatformInviteRejectRequest,
)
from app.platform_invite.query import (
    create_query,
    read_query,
    read_by_id_query,
    read_by_token_hash_query,
    update_status_query,
    mark_expired_query,
    hash_token,
)
from app.user.model import SignupRequest
from app.user.query import signup_query
from app.platform_user.model import PlatformUserCreateRequest
from app.platform_user.service import create_service as create_platform_user_service
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest, PyObjectId
from pwdlib import PasswordHash
import secrets


def generate_invite_token() -> str:
    """Generate a random token for platform invite (MDC-PU-S-4: raw_invite_tokens_are_never_stored)"""
    return secrets.token_urlsafe(32)  # 32 bytes = 43 characters URL-safe


async def create_invite_service(
    invite: PlatformInviteCreateRequest,
    invited_by_user_id: str
) -> dict:
    """
    Create a platform invite
    
    Following MDC-PU invite_creation:
    - Generate random token
    - Store hash in PLATFORM_INVITE
    - Send raw token via email (for now, return it)
    - Status = pending
    """
    # Generate random token
    raw_token = generate_invite_token()
    token_hash = hash_token(raw_token)
    
    # Calculate expiration
    expires_at = datetime.now(timezone.utc) + timedelta(days=invite.expires_in_days)
    
    # Create invite with hashed token
    invite_id = await create_query(
        invite,
        token_hash,
        PyObjectId(invited_by_user_id),
        expires_at
    )
    
    # TODO: Send raw token via email
    # For now, return it in the response (should be removed in production)
    return {
        "invite_id": str(invite_id),
        "token": raw_token,  # Only returned for development - should be sent via email
        "expires_at": expires_at.isoformat(),
    }


async def validate_invite_service(token: str) -> PlatformInviteValidateResponse:
    """
    Validate an invite token
    
    Following MDC-PU invite_validation:
    - Hash token
    - Find pending invite by hash
    - Ensure not expired
    """
    # Mark expired invites first
    await mark_expired_query()
    
    # Hash the token
    token_hash = hash_token(token)
    
    # Find invite by hash
    invite = await read_by_token_hash_query(token_hash)
    
    if not invite:
        return PlatformInviteValidateResponse(
            valid=False,
            message="Invalid invite token"
        )
    
    # Check status
    if invite.status != "PENDING":
        return PlatformInviteValidateResponse(
            valid=False,
            message=f"Invite has been {invite.status}"
        )
    
    # Check expiration
    if invite.expires_at < datetime.now(timezone.utc):
        # Mark as expired
        await update_status_query(str(invite.id), "expired")
        return PlatformInviteValidateResponse(
            valid=False,
            message="Invite has expired"
        )
    
    return PlatformInviteValidateResponse(
        valid=True,
        invite=invite,
        message="Invite is valid"
    )


async def accept_invite_service(accept_request: PlatformInviteAcceptRequest) -> Response:
    """
    Accept a platform invite
    
    Following MDC-PU invite_acceptance:
    - Validate invite
    - Create USER
    - Create PLATFORM_USER
    - Mark invite accepted
    - Invalidate token
    """
    # Validate invite
    validation = await validate_invite_service(accept_request.token)
    if not validation.valid or not validation.invite:
        raise HTTPException(
            status_code=400,
            detail=validation.message or "Invalid invite token"
        )
    
    invite = validation.invite
    
    # Check if user already exists with this email
    from app.user.query import read_by_email_query
    existing_user = await read_by_email_query(invite.email)
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists"
        )
    
    # Create USER (MDC-PU-S-1: identity_created_only_on_acceptance)
    password_hash = PasswordHash.recommended()
    hashed_password = password_hash.hash(accept_request.password)
    
    signup_data = SignupRequest(
        first_name=accept_request.first_name,
        last_name=accept_request.last_name,
        email=invite.email,  # Use email from invite
        password=hashed_password,
        status="ACTIVE"
    )
    
    user_id = await signup_query(signup_data)
    
    # Create PLATFORM_USER
    platform_user_data = PlatformUserCreateRequest(
        user_id=user_id,
        platform_privilege_set_id=invite.platform_privilege_set_id,
        status="ACTIVE"
    )
    
    await create_platform_user_service(platform_user_data)
    
    # Mark invite as accepted
    await update_status_query(
        str(invite.id),
        "accepted",
        accepted_at=datetime.now(timezone.utc)
    )
    
    return Response(status_code=201)


async def reject_invite_service(reject_request: PlatformInviteRejectRequest) -> Response:
    """
    Reject a platform invite
    
    Following MDC-PU invite_rejection:
    - Mark invite rejected
    - Invalidate token
    """
    # Validate invite
    validation = await validate_invite_service(reject_request.token)
    if not validation.valid or not validation.invite:
        raise HTTPException(
            status_code=400,
            detail=validation.message or "Invalid invite token"
        )
    
    invite = validation.invite
    
    # Mark invite as rejected
    await update_status_query(str(invite.id), "rejected")
    
    return Response(status_code=200)


async def read_service(params: ParamRequest) -> PaginatedResponse[PlatformInvite]:
    """Read platform invites (paginated)"""
    invites = await read_query(params)
    return PaginatedResponse[PlatformInvite](
        status_code=200,
        message="Successful",
        data=invites.data,
        pagination=invites.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[PlatformInvite]:
    """Read a platform invite by ID"""
    invite = await read_by_id_query(id)
    if invite is None:
        raise HTTPException(status_code=404, detail="Platform invite not found")
    return BaseResponse[PlatformInvite](status_code=200, message="Successful", data=invite)

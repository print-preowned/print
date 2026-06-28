from datetime import datetime, timezone, timedelta
from bson import ObjectId
from fastapi import HTTPException, Response
from app.platform_invite.model import (
    PlatformInvite,
    PlatformInviteCreateRequest,
    PlatformInviteResendRequest,
    PlatformInviteValidateResponse,
    PlatformInviteAcceptRequest,
    PlatformInviteRejectRequest,
    PlatformInviteWithPrivilegeSet,
)
from app.platform_invite.query import (
    create_query,
    read_query,
    read_by_id_query,
    read_by_token_hash_query,
    read_pending_by_email_query,
    resend_pending_query,
    update_status_query,
    mark_expired_query,
    hash_token,
)
from app.user.model import SignupRequest
from app.user.query import read_by_email_query, signup_query
from app.platform_user.model import PlatformUserCreateRequest
from app.platform_user.query import read_by_user_id_query
from app.platform_user.service import create_service as create_platform_user_service
from app.platform_user.guards import ensure_super_admin_not_invitable
from app.platform_privilege_set.query import read_by_ids_query as read_privilege_sets_by_ids
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest, PyObjectId
from app.utility.email import EmailDeliveryError, send_platform_invite_email
from pwdlib import PasswordHash
import secrets

INVITE_EXPIRY_DAYS = 7


def generate_invite_token() -> str:
    """Generate a random token for platform invite (MDC-PU-S-4: raw_invite_tokens_are_never_stored)"""
    return secrets.token_urlsafe(32)  # 32 bytes = 43 characters URL-safe


def _email_invite(*, email: str, raw_token: str, expires_at: datetime) -> None:
    try:
        send_platform_invite_email(
            to=email,
            raw_token=raw_token,
            expires_at_iso=expires_at.isoformat(),
        )
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc


def _new_invite_token() -> tuple[str, str]:
    raw_token = generate_invite_token()
    return raw_token, hash_token(raw_token)


async def _require_pending_invite(invite_id: str) -> PlatformInvite:
    await mark_expired_query()
    invite = await read_by_id_query(invite_id)
    if invite is None:
        raise HTTPException(status_code=404, detail="Platform invite not found")
    if invite.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail=f"Invite is {invite.status.lower()} and cannot be modified",
        )
    if invite.expires_at < datetime.now(timezone.utc):
        await update_status_query(invite_id, "EXPIRED")
        raise HTTPException(status_code=409, detail="Invite has expired")
    return invite


async def _ensure_email_not_platform_user(email: str) -> None:
    user = await read_by_email_query(email)
    if user is None:
        return
    platform_user = await read_by_user_id_query(str(user.id))
    if platform_user is not None:
        raise HTTPException(
            status_code=409,
            detail=f"{email} already has platform access",
        )


def _invite_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRY_DAYS)


async def create_invite_service(
    invite: PlatformInviteCreateRequest,
    invited_by_user_id: str
) -> dict:
    """
    Create a platform invite

    Following MDC-PU invite_creation:
    - Generate random token
    - Store hash in PLATFORM_INVITE
    - Send raw token via email (never returned in API response)
    - Status = PENDING
    """
    await mark_expired_query()

    await _ensure_email_not_platform_user(invite.email)

    existing = await read_pending_by_email_query(invite.email)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A pending invitation already exists for {invite.email}",
        )

    await ensure_super_admin_not_invitable(str(invite.platform_privilege_set_id))

    expires_at = _invite_expires_at()
    raw_token, token_hash = _new_invite_token()

    invite_id = await create_query(
        invite,
        token_hash,
        PyObjectId(invited_by_user_id),
        expires_at
    )

    try:
        _email_invite(email=invite.email, raw_token=raw_token, expires_at=expires_at)
    except HTTPException:
        await update_status_query(str(invite_id), "REVOKED")
        raise

    expires_at_iso = expires_at.isoformat()

    return {
        "invite_id": str(invite_id),
        "expires_at": expires_at_iso,
        "message": f"Invitation email sent to {invite.email}",
    }


async def resend_invite_service(
    invite_id: str,
    body: PlatformInviteResendRequest,
    admin_user_id: str,
) -> dict:
    """
    Resend a pending invite with a new token and optional privilege set change.
    Invalidates any previous accept/reject links for this invite.
    """
    invite = await _require_pending_invite(invite_id)

    privilege_set_id = body.platform_privilege_set_id or invite.platform_privilege_set_id
    await ensure_super_admin_not_invitable(str(privilege_set_id))

    expires_at = _invite_expires_at()
    raw_token, token_hash = _new_invite_token()

    updated = await resend_pending_query(
        invite_id,
        token_hash=token_hash,
        platform_privilege_set_id=ObjectId(privilege_set_id),
        expires_at=expires_at,
        updated_by=PyObjectId(admin_user_id),
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail="Invite is no longer pending and could not be resent",
        )

    try:
        _email_invite(email=invite.email, raw_token=raw_token, expires_at=expires_at)
    except HTTPException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=(
                f"{exc.detail} The invite token was updated; use Resend again after "
                "fixing mail delivery."
            ),
        ) from exc

    expires_at_iso = expires_at.isoformat()
    return {
        "invite_id": invite_id,
        "expires_at": expires_at_iso,
        "message": f"Invitation resent to {invite.email}",
    }


async def revoke_invite_service(invite_id: str) -> Response:
    """Revoke a pending invite (admin). Invalidates the invite token without notifying the invitee."""
    invite = await _require_pending_invite(invite_id)
    await update_status_query(str(invite.id), "REVOKED")
    return Response(status_code=200)


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
        await update_status_query(str(invite.id), "EXPIRED")
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
        user_id=PyObjectId(user_id),
        platform_privilege_set_id=invite.platform_privilege_set_id,
        status="ACTIVE"
    )
    
    await create_platform_user_service(platform_user_data)
    
    # Mark invite as accepted
    await update_status_query(
        str(invite.id),
        "ACCEPTED",
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
    await update_status_query(str(invite.id), "REJECTED")
    
    return Response(status_code=200)


async def read_service(params: ParamRequest) -> PaginatedResponse[PlatformInviteWithPrivilegeSet]:
    """Read platform invites (paginated)"""
    invites = await read_query(params)
    if not invites.data:
        return PaginatedResponse[PlatformInviteWithPrivilegeSet](
            status_code=200,
            message="Successful",
            data=[],
            pagination=invites.pagination,
        )

    privilege_set_ids = list(
        {str(inv.platform_privilege_set_id) for inv in invites.data}
    )
    privilege_set_docs = await read_privilege_sets_by_ids(privilege_set_ids)
    privilege_set_map = {str(ps.id): ps.name for ps in privilege_set_docs}

    data = []
    for inv in invites.data:
        data.append(
            PlatformInviteWithPrivilegeSet(
                **inv.model_dump(mode="json"),
                platform_privilege_set_name=privilege_set_map.get(
                    str(inv.platform_privilege_set_id), "—"
                ),
            )
        )

    return PaginatedResponse[PlatformInviteWithPrivilegeSet](
        status_code=200,
        message="Successful",
        data=data,
        pagination=invites.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[PlatformInvite]:
    """Read a platform invite by ID"""
    invite = await read_by_id_query(id)
    if invite is None:
        raise HTTPException(status_code=404, detail="Platform invite not found")
    return BaseResponse[PlatformInvite](status_code=200, message="Successful", data=invite)

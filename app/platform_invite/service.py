from __future__ import annotations

import math
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Response
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_invite.model import (
    PlatformInviteAcceptRequest,
    PlatformInviteCreateRequest,
    PlatformInviteRejectRequest,
    PlatformInviteResendRequest,
    PlatformInviteSummary,
    PlatformInviteValidateResponse,
    PlatformInviteWithPrivilegeSet,
)
from app.platform_invite.query import hash_token
from app.platform_invite.repository import (
    count_platform_invites,
    create_platform_invite,
    list_platform_invites,
    mark_expired_invites,
    read_pending_invite_by_email,
    read_platform_invite_by_id,
    read_platform_invite_by_token_hash,
    resend_pending_invite,
    update_invite_status,
)
from app.platform_invite.schemas import PlatformInviteCreate, PlatformInviteRead
from app.platform_privilege_set.query import read_by_ids_query as read_privilege_sets_by_ids
from app.platform_user.guards import ensure_super_admin_not_invitable
from app.platform_user.model import PlatformUserCreateRequest
from app.platform_user.service import PlatformUserService
from app.user.model import SignupRequest
from app.user.query import read_by_email_query, signup_query
from app.platform_user.query import read_by_user_id_query
from app.utility.email import EmailDeliveryError, send_platform_invite_email
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service

INVITE_EXPIRY_DAYS = 7


def generate_invite_token() -> str:
    """Generate a random token for platform invite (MDC-PU-S-4: raw_invite_tokens_are_never_stored)"""
    return secrets.token_urlsafe(32)


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PlatformInviteRead:
    return PlatformInviteRead.model_validate(row)


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


def _invite_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRY_DAYS)


class PlatformInviteService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _mark_expired(self) -> None:
        await mark_expired_invites(self._session)

    async def _require_pending_invite(self, invite_id: str) -> PlatformInviteRead:
        await self._mark_expired()
        row = await read_platform_invite_by_id(self._session, _parse_id(invite_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Platform invite not found")
        invite = _to_read(row)
        if invite.status != "PENDING":
            raise HTTPException(
                status_code=409,
                detail=f"Invite is {invite.status.lower()} and cannot be modified",
            )
        if invite.expires_at < datetime.now(timezone.utc):
            await update_invite_status(self._session, invite.id, "EXPIRED")
            raise HTTPException(status_code=409, detail="Invite has expired")
        return invite

    async def _ensure_email_not_platform_user(self, email: str) -> None:
        user = await read_by_email_query(email)
        if user is None:
            return
        platform_user = await read_by_user_id_query(str(user.id))
        if platform_user is not None:
            raise HTTPException(
                status_code=409,
                detail=f"{email} already has platform access",
            )

    async def create_invite(
        self,
        invite: PlatformInviteCreateRequest,
        invited_by_user_id: str,
    ) -> dict:
        await self._mark_expired()
        await self._ensure_email_not_platform_user(invite.email)

        existing_row = await read_pending_invite_by_email(self._session, invite.email)
        if existing_row:
            raise HTTPException(
                status_code=409,
                detail=f"A pending invitation already exists for {invite.email}",
            )

        await ensure_super_admin_not_invitable(str(invite.platform_privilege_set_id))

        expires_at = _invite_expires_at()
        raw_token, token_hash = _new_invite_token()

        payload = PlatformInviteCreate(
            email=invite.email,
            platform_privilege_set_id=uuid.UUID(str(invite.platform_privilege_set_id)),
        )
        created = await create_platform_invite(
            self._session,
            payload=payload,
            token_hash=token_hash,
            invited_by=uuid.UUID(str(invited_by_user_id)),
            expires_at=expires_at,
        )

        try:
            _email_invite(email=invite.email, raw_token=raw_token, expires_at=expires_at)
        except HTTPException:
            await update_invite_status(self._session, created.id, "REVOKED")
            raise

        return {
            "invite_id": str(created.id),
            "expires_at": expires_at.isoformat(),
            "message": f"Invitation email sent to {invite.email}",
        }

    async def resend_invite(
        self,
        invite_id: str,
        body: PlatformInviteResendRequest,
        admin_user_id: str,
    ) -> dict:
        invite = await self._require_pending_invite(invite_id)

        privilege_set_id = body.platform_privilege_set_id or invite.platform_privilege_set_id
        await ensure_super_admin_not_invitable(str(privilege_set_id))

        expires_at = _invite_expires_at()
        raw_token, token_hash = _new_invite_token()

        updated = await resend_pending_invite(
            self._session,
            _parse_id(invite_id),
            token_hash=token_hash,
            platform_privilege_set_id=uuid.UUID(str(privilege_set_id)),
            expires_at=expires_at,
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

        return {
            "invite_id": invite_id,
            "expires_at": expires_at.isoformat(),
            "message": f"Invitation resent to {invite.email}",
        }

    async def revoke_invite(self, invite_id: str) -> Response:
        invite = await self._require_pending_invite(invite_id)
        await update_invite_status(self._session, invite.id, "REVOKED")
        return Response(status_code=200)

    async def validate_invite(self, token: str) -> PlatformInviteValidateResponse:
        await self._mark_expired()

        token_hash = hash_token(token)
        row = await read_platform_invite_by_token_hash(self._session, token_hash)

        if not row:
            return PlatformInviteValidateResponse(
                valid=False,
                message="Invalid invite token",
            )

        invite = _to_read(row)

        if invite.status != "PENDING":
            return PlatformInviteValidateResponse(
                valid=False,
                message=f"Invite has been {invite.status}",
            )

        if invite.expires_at < datetime.now(timezone.utc):
            await update_invite_status(self._session, invite.id, "EXPIRED")
            return PlatformInviteValidateResponse(
                valid=False,
                message="Invite has expired",
            )

        return PlatformInviteValidateResponse(
            valid=True,
            invite=PlatformInviteSummary(
                id=str(invite.id),
                email=invite.email,
                platform_privilege_set_id=str(invite.platform_privilege_set_id),
                expires_at=invite.expires_at,
                status=invite.status,
                invited_by=str(invite.invited_by),
                created_at=invite.created_at,
                accepted_at=invite.accepted_at,
            ),
            message="Invite is valid",
        )

    async def accept_invite(self, accept_request: PlatformInviteAcceptRequest) -> Response:
        validation = await self.validate_invite(accept_request.token)
        if not validation.valid or not validation.invite:
            raise HTTPException(
                status_code=400,
                detail=validation.message or "Invalid invite token",
            )

        invite = validation.invite

        existing_user = await read_by_email_query(invite.email)
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="A user with this email already exists",
            )

        password_hash = PasswordHash.recommended()
        hashed_password = password_hash.hash(accept_request.password)

        signup_data = SignupRequest(
            first_name=accept_request.first_name,
            last_name=accept_request.last_name,
            email=invite.email,
            password=hashed_password,
            status="ACTIVE",
        )

        user_id = await signup_query(signup_data)

        platform_user_data = PlatformUserCreateRequest(
            user_id=user_id,
            platform_privilege_set_id=invite.platform_privilege_set_id,
            status="ACTIVE",
        )

        await PlatformUserService(self._session).create(platform_user_data)

        await update_invite_status(
            self._session,
            _parse_id(str(invite.id)),
            "ACCEPTED",
            accepted_at=datetime.now(timezone.utc),
        )

        return Response(status_code=201)

    async def reject_invite(self, reject_request: PlatformInviteRejectRequest) -> Response:
        validation = await self.validate_invite(reject_request.token)
        if not validation.valid or not validation.invite:
            raise HTTPException(
                status_code=400,
                detail=validation.message or "Invalid invite token",
            )

        invite = validation.invite
        await update_invite_status(self._session, _parse_id(str(invite.id)), "REJECTED")
        return Response(status_code=200)

    async def read(self, params: ParamRequest) -> PaginatedResponse[PlatformInviteWithPrivilegeSet]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await count_platform_invites(self._session)
        rows = await list_platform_invites(self._session, offset=offset, limit=size)
        invites = [_to_read(row) for row in rows]

        if not invites:
            total_pages = math.ceil(total_results / size) if size else 1
            return PaginatedResponse[PlatformInviteWithPrivilegeSet](
                status_code=200,
                message="Successful",
                data=[],
                pagination=Pagination(
                    page=page,
                    size=size,
                    total_pages=total_pages,
                    total_results=total_results,
                ),
            )

        privilege_set_ids = list(
            {str(inv.platform_privilege_set_id) for inv in invites}
        )
        privilege_set_docs = await read_privilege_sets_by_ids(privilege_set_ids)
        privilege_set_map = {str(ps.id): ps.name for ps in privilege_set_docs}

        data = []
        for inv in invites:
            data.append(
                PlatformInviteWithPrivilegeSet(
                    **inv.model_dump(mode="json"),
                    platform_privilege_set_name=privilege_set_map.get(
                        str(inv.platform_privilege_set_id), "—"
                    ),
                )
            )

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[PlatformInviteWithPrivilegeSet](
            status_code=200,
            message="Successful",
            data=data,
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id(self, id: str) -> BaseResponse[PlatformInviteRead]:
        row = await read_platform_invite_by_id(self._session, _parse_id(id))
        if row is None:
            raise HTTPException(status_code=404, detail="Platform invite not found")
        return BaseResponse[PlatformInviteRead](status_code=200, message="Successful", data=_to_read(row))


class WritablePlatformInviteService(writable_service(PlatformInviteService)):
    pass


class ReadablePlatformInviteService(readable_service(PlatformInviteService)):
    pass

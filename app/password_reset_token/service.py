from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Response
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from app.password_reset_token.model import (
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordResetCompleteRequest,
    PasswordResetRequest,
    PasswordResetValidateResponse,
)
from app.password_reset_token.query import hash_token
from app.password_reset_token.repository import PasswordResetTokenRepository
from app.password_reset_token.schemas import PasswordResetTokenCreate
from app.platform_privilege_set_privilege.query import read_by_privilege_set_id_query
from app.platform_user.query import read_by_user_id_query as read_platform_user_by_user_id_query
from app.user.repository import UserRepository
from app.user.schemas import UserUpdate
from app.utility.authorization import TokenPayload
from app.utility.service_deps import readable_service, writable_service
from app.utility.token import create_platform_token


def generate_reset_token() -> str:
    """Generate a random token for password reset"""
    return secrets.token_urlsafe(32)


def _parse_user_id(user_id: str) -> uuid.UUID:
    return uuid.UUID(user_id)


class PasswordResetTokenService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PasswordResetTokenRepository(session)
        self._user_repo = UserRepository(session)

    async def request_password_reset(self, request: PasswordResetRequest) -> dict:
        row = await self._user_repo.read_user_by_email(request.email)
        if not row:
            return {
                "message": "If an account with that email exists, a password reset link has been sent."
            }

        raw_token = generate_reset_token()
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        await self._repo.create_password_reset_token(
            PasswordResetTokenCreate(
                user_id=row.id,
                token_hash=token_hash,
                expires_at=expires_at,
            ),
        )

        return {
            "message": "If an account with that email exists, a password reset link has been sent.",
            "token": raw_token,
            "expires_at": expires_at.isoformat(),
        }

    async def validate_reset_token(self, token: str) -> PasswordResetValidateResponse:
        token_hash = hash_token(token)
        row = await self._repo.read_password_reset_token_by_hash(token_hash)

        if not row:
            return PasswordResetValidateResponse(
                valid=False,
                message="Invalid or expired reset token",
            )

        if row.used:
            return PasswordResetValidateResponse(
                valid=False,
                message="This reset token has already been used",
            )

        if row.expires_at < datetime.now(timezone.utc):
            return PasswordResetValidateResponse(
                valid=False,
                message="This reset token has expired",
            )

        return PasswordResetValidateResponse(
            valid=True,
            message="Token is valid",
        )

    async def complete_password_reset(
        self, complete_request: PasswordResetCompleteRequest
    ) -> Response:
        validation = await self.validate_reset_token(complete_request.token)
        if not validation.valid:
            raise HTTPException(
                status_code=400,
                detail=validation.message or "Invalid or expired reset token",
            )

        token_hash = hash_token(complete_request.token)
        reset_token = await self._repo.read_password_reset_token_by_hash(token_hash)
        if not reset_token:
            raise HTTPException(status_code=400, detail="Invalid reset token")

        password_hash = PasswordHash.recommended()
        hashed_password = password_hash.hash(complete_request.new_password)

        updated = await self._user_repo.update_user(
            reset_token.user_id,
            UserUpdate(password=hashed_password),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="User not found")

        marked = await self._repo.mark_password_reset_token_used(reset_token.id)
        if not marked:
            raise HTTPException(status_code=400, detail="Invalid reset token")

        return Response(status_code=200)

    async def change_password(
        self,
        token_payload: TokenPayload,
        change_request: PasswordChangeRequest,
    ) -> PasswordChangeResponse:
        user_id = token_payload.sub
        parsed_user_id = _parse_user_id(user_id)

        row = await self._user_repo.read_user_by_id(parsed_user_id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        password_hash = PasswordHash.recommended()
        is_valid = password_hash.verify(change_request.current_password, row.password)
        if not is_valid:
            raise HTTPException(status_code=403, detail="Current password is incorrect")

        was_new = row.status == "NEW"
        hashed_password = password_hash.hash(change_request.new_password)

        updated = await self._user_repo.update_user(
            parsed_user_id,
            UserUpdate(password=hashed_password),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="User not found")

        if was_new:
            status_updated = await self._user_repo.update_user(
                parsed_user_id,
                UserUpdate(status="ACTIVE"),
            )
            if status_updated is None:
                raise HTTPException(status_code=404, detail="User not found")

        new_token: str | None = None
        if token_payload.ctx == "PLATFORM":
            platform_user = await read_platform_user_by_user_id_query(user_id)
            if platform_user:
                privilege_mappings = await read_by_privilege_set_id_query(
                    str(platform_user.platform_privilege_set_id)
                )
                privileges = [mapping.privilege_code for mapping in privilege_mappings]
                updated_row = await self._user_repo.read_user_by_id(parsed_user_id)
                if updated_row:
                    from app.user.schemas import UserRead

                    new_token = create_platform_token(
                        UserRead.model_validate(updated_row),
                        privileges,
                        password_change_required=False,
                    )

        return PasswordChangeResponse(token=new_token)


class WritablePasswordResetTokenService(writable_service(PasswordResetTokenService)):
    pass


class ReadablePasswordResetTokenService(readable_service(PasswordResetTokenService)):
    pass

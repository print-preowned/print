"""Token revocation via Redis jti blocklist (MDC-REVOKE-1)."""

from __future__ import annotations

import time
import uuid

from app.user.repository import UserRepository
from app.utility.authorization import TokenPayload
from app.utility.redis import get_key, set_key
from app.utility.token import decode_token


def _redis_value_to_str(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode()
    return str(value)


def revoke_jti(jti: str, exp: int) -> None:
    ttl = max(int(exp) - int(time.time()), 1)
    set_key(f"revoked:{jti}", "1", ex=ttl)


def revoke_token_string(token: str) -> None:
    payload = decode_token(token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp is not None:
        revoke_jti(str(jti), int(exp))


def revoke_token_payload(token: TokenPayload) -> None:
    if token.jti and token.exp is not None:
        revoke_jti(str(token.jti), int(token.exp))


async def revoke_user_active_session(user_repo: UserRepository, user_id: uuid.UUID) -> None:
    row = await user_repo.read_user_by_id(user_id)
    if row is None:
        return
    stored = _redis_value_to_str(get_key(row.email))
    if stored:
        revoke_token_string(stored)


async def revoke_role_active_sessions(
    business_user_repo,
    user_repo: UserRepository,
    role_id: uuid.UUID,
) -> None:
    """Revoke active sessions for every member assigned to role_id (MDC-REVOKE-1)."""
    user_ids = await business_user_repo.read_user_ids_by_role_id(role_id)
    for user_id in user_ids:
        await revoke_user_active_session(user_repo, user_id)

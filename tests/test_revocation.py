"""Token revocation unit tests (no database or Redis required)."""

from __future__ import annotations

import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.utility.authorization import TokenPayload, get_token_payload
from app.utility.revocation import (
    revoke_jti,
    revoke_role_active_sessions,
    revoke_token_payload,
    revoke_user_active_session,
)


def test_revoke_jti_sets_redis_blocklist_entry() -> None:
    exp = int(time.time()) + 3600
    with patch("app.utility.revocation.set_key") as mock_set_key:
        revoke_jti("jti-abc", exp)

    mock_set_key.assert_called_once()
    key, value = mock_set_key.call_args[0]
    assert key == "revoked:jti-abc"
    assert value == "1"
    assert mock_set_key.call_args[1]["ex"] >= 1


def test_revoke_token_payload_uses_jti_and_exp() -> None:
    token = TokenPayload(
        {
            "iss": "print-api",
            "aud": "print-web",
            "sub": str(uuid.uuid4()),
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "jti": "payload-jti",
            "ctx": "BUSINESS",
            "business": {"id": "b1", "privileges": ["READ_BOOK"], "is_owner": True},
        }
    )
    with patch("app.utility.revocation.revoke_jti") as mock_revoke_jti:
        revoke_token_payload(token)

    mock_revoke_jti.assert_called_once_with("payload-jti", token.exp)


@pytest.mark.asyncio
async def test_revoke_user_active_session_revokes_stored_token() -> None:
    user_id = uuid.uuid4()
    user_row = MagicMock()
    user_row.email = "staff@example.com"
    user_repo = AsyncMock()
    user_repo.read_user_by_id = AsyncMock(return_value=user_row)

    with (
        patch("app.utility.revocation.get_key", return_value="stored-jwt"),
        patch("app.utility.revocation.revoke_token_string") as mock_revoke_token,
    ):
        await revoke_user_active_session(user_repo, user_id)

    mock_revoke_token.assert_called_once_with("stored-jwt")


@pytest.mark.asyncio
async def test_revoke_role_active_sessions_revokes_each_member() -> None:
    role_id = uuid.uuid4()
    user_ids = [uuid.uuid4(), uuid.uuid4()]
    business_user_repo = AsyncMock()
    business_user_repo.read_user_ids_by_role_id = AsyncMock(return_value=user_ids)
    user_repo = AsyncMock()

    with patch(
        "app.utility.revocation.revoke_user_active_session",
        new_callable=AsyncMock,
    ) as mock_revoke_user:
        await revoke_role_active_sessions(business_user_repo, user_repo, role_id)

    assert mock_revoke_user.await_count == 2
    business_user_repo.read_user_ids_by_role_id.assert_awaited_once_with(role_id)


@pytest.mark.asyncio
async def test_get_token_payload_rejects_revoked_jti() -> None:
    request = MagicMock()
    request.headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "iss": "print-api",
        "aud": "print-web",
        "sub": str(uuid.uuid4()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "jti": "revoked-jti",
        "ctx": "CUSTOMER",
        "has_business": False,
    }

    with (
        patch("app.utility.authorization.decode_token", return_value=payload),
        patch("app.utility.authorization.get_key", return_value=b"1"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_token_payload(request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has been revoked"

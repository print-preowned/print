"""Business delete revocation and token reissue tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.business.service import BusinessService
from app.utility.authorization import TokenPayload


def _customer_token_payload(user_id: uuid.UUID) -> TokenPayload:
    return TokenPayload(
        {
            "iss": "print-api",
            "aud": "print-web",
            "sub": str(user_id),
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int(datetime.now(UTC).timestamp()) + 3600,
            "jti": "delete-actor-jti",
            "ctx": "BUSINESS",
            "business": {
                "id": str(uuid.uuid4()),
                "privileges": ["DELETE_BUSINESS"],
                "is_owner": True,
            },
        }
    )


def _user_row(user_id: uuid.UUID, email: str = "owner@example.com") -> MagicMock:
    row = MagicMock()
    row.id = user_id
    row.role_id = None
    row.first_name = "Owner"
    row.last_name = "User"
    row.middle_name = None
    row.country_code = None
    row.phone_number = None
    row.email = email
    row.profile_image = None
    row.password = "hashed"
    row.status = "ACTIVE"
    row.created_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)
    return row


@pytest.mark.asyncio
async def test_business_delete_revokes_members_and_reissues_customer_token() -> None:
    business_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    staff_id = uuid.uuid4()
    token = _customer_token_payload(owner_id)

    business_row = MagicMock()
    business_row.user_id = owner_id

    member_owner = MagicMock()
    member_owner.user_id = owner_id
    member_staff = MagicMock()
    member_staff.user_id = staff_id
    members = [member_owner, member_staff]

    session = AsyncMock()
    service = BusinessService(session)
    service._repo = AsyncMock()
    service._user_repo = AsyncMock()
    service._business_user_repo = AsyncMock()

    service._repo.read_by_id = AsyncMock(return_value=business_row)
    service._repo.delete = AsyncMock(return_value=True)
    service._business_user_repo.read_business_users_by_business_id = AsyncMock(
        return_value=members
    )
    service._business_user_repo.delete_by_business_id = AsyncMock(return_value=2)
    service._user_repo.read_user_by_id = AsyncMock(return_value=_user_row(owner_id))

    with (
        patch(
            "app.business.service.revoke_user_active_session",
            new_callable=AsyncMock,
        ) as mock_revoke_user,
        patch("app.business.service.revoke_token_payload") as mock_revoke_token,
        patch(
            "app.business.service.create_customer_token",
            return_value="new-customer-token",
        ) as mock_create_token,
        patch("app.business.service.set_key") as mock_set_key,
    ):
        result = await service.delete(str(business_id), token)

    assert result.token == "new-customer-token"
    assert mock_revoke_user.await_count == 2
    mock_revoke_token.assert_called_once_with(token)
    mock_create_token.assert_called_once()
    _, kwargs = mock_create_token.call_args
    assert kwargs.get("has_business") is False
    mock_set_key.assert_called_once_with("owner@example.com", "new-customer-token", 60 * 60 * 24)

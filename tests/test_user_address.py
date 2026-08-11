"""User address validation and service tests."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.user_address.model import UserAddressCreateRequest, UserAddressUpdateRequest
from app.user_address.orm import UserAddressOrm
from app.user_address.repository import UserAddressRepository
from app.user_address.service import UserAddressService
from app.utility.address import validate_nigeria_address_fields, validate_phone_number


def _address_row(user_id: uuid.UUID, **overrides: object) -> MagicMock:
    row = MagicMock(spec=UserAddressOrm)
    values = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "label": "Home",
        "recipient_name": "Jane Doe",
        "phone_number": "+2348012345678",
        "line1": "12 Allen Avenue",
        "line2": None,
        "city": "Ikeja",
        "state": "Lagos",
        "postal_code": None,
        "country_code": "NG",
        "is_default": True,
        **overrides,
    }
    for key, value in values.items():
        setattr(row, key, value)
    return row


class TestAddressValidation:
    def test_validate_nigeria_address_accepts_lagos(self) -> None:
        result = validate_nigeria_address_fields(
            line1="12 Allen Avenue",
            city="Ikeja",
            state="Lagos",
            country_code="NG",
            phone_number="08012345678",
        )
        assert result["state"] == "Lagos"
        assert result["country_code"] == "NG"
        assert result["phone_number"] == "+2348012345678"

    def test_validate_nigeria_address_accepts_international_phone(self) -> None:
        result = validate_nigeria_address_fields(
            line1="12 Allen Avenue",
            city="Ikeja",
            state="Lagos",
            phone_number="+14155552671",
        )
        assert result["phone_number"] == "+14155552671"

    def test_validate_nigeria_address_rejects_invalid_state(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_nigeria_address_fields(
                line1="12 Allen Avenue",
                city="Ikeja",
                state="Invalid",
            )
        assert exc.value.status_code == 422

    def test_validate_nigeria_address_rejects_non_ng_country(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_nigeria_address_fields(
                line1="12 Allen Avenue",
                city="London",
                state="Lagos",
                country_code="GB",
            )
        assert exc.value.status_code == 422

    def test_validate_phone_number_normalizes_local_format(self) -> None:
        assert validate_phone_number("08012345678") == "+2348012345678"

    def test_validate_phone_number_normalizes_country_code_without_plus(self) -> None:
        assert validate_phone_number("2348012345678") == "+2348012345678"

    def test_validate_phone_number_accepts_international_format(self) -> None:
        assert validate_phone_number("+2348012345678") == "+2348012345678"
        assert validate_phone_number("+14155552671") == "+14155552671"

    def test_validate_phone_number_accepts_spaced_input(self) -> None:
        from app.utility.address import normalize_phone_input

        assert normalize_phone_input("080 1234 5678") == "08012345678"

    def test_validate_phone_number_rejects_invalid(self) -> None:
        with pytest.raises(HTTPException):
            validate_phone_number("abc")

    def test_validate_phone_number_rejects_non_mobile_prefix(self) -> None:
        with pytest.raises(HTTPException):
            validate_phone_number("06012345678")

    def test_validate_phone_number_rejects_international_without_plus(self) -> None:
        with pytest.raises(HTTPException):
            validate_phone_number("14155552671")

    def test_validate_phone_number_required(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_phone_number(None, required=True)
        assert exc.value.detail == "Phone number is required"


@pytest.mark.asyncio
async def test_user_address_create_auto_defaults_first_address() -> None:
    user_id = uuid.uuid4()
    session = AsyncMock()
    service = UserAddressService(session)
    service._repo = AsyncMock()
    service._repo.count_active_by_user = AsyncMock(return_value=0)
    service._repo.clear_default_for_user = AsyncMock()
    created_row = _address_row(user_id=user_id)
    service._repo.create = AsyncMock(return_value=created_row)

    payload = UserAddressCreateRequest(
        recipient_name="Jane Doe",
        phone_number="08012345678",
        line1="12 Allen Avenue",
        city="Ikeja",
        state="Lagos",
    )

    result = await service.create(payload, str(user_id))

    assert result.status_code == 201
    service._repo.clear_default_for_user.assert_not_awaited()
    create_arg = service._repo.create.await_args.args[0]
    assert create_arg.is_default is True
    assert create_arg.user_id == user_id


@pytest.mark.asyncio
async def test_user_address_delete_only_address_is_blocked() -> None:
    user_id = uuid.uuid4()
    address_id = uuid.uuid4()
    session = AsyncMock()
    service = UserAddressService(session)
    service._repo = AsyncMock()
    row = MagicMock(spec=UserAddressOrm)
    row.is_default = True
    service._repo.read_by_id = AsyncMock(return_value=row)
    service._repo.count_active_by_user = AsyncMock(return_value=1)

    with pytest.raises(HTTPException) as exc:
        await service.delete(str(address_id), str(user_id))

    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_user_address_set_default_not_found() -> None:
    service = UserAddressService(AsyncMock())
    service._repo = AsyncMock()
    service._repo.set_default = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.set_default(str(uuid.uuid4()), str(uuid.uuid4()))

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_user_address_repository_soft_delete() -> None:
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=uuid.uuid4())
    deleted = await UserAddressRepository(session).delete(uuid.uuid4(), uuid.uuid4())
    assert deleted is True


@pytest.mark.asyncio
async def test_user_address_update_merges_address_fields() -> None:
    user_id = uuid.uuid4()
    address_id = uuid.uuid4()
    session = AsyncMock()
    service = UserAddressService(session)
    service._repo = AsyncMock()

    row = _address_row(
        id=address_id,
        user_id=user_id,
        phone_number="08012345678",
    )
    service._repo.read_by_id = AsyncMock(return_value=row)

    updated_row = _address_row(
        id=address_id,
        user_id=user_id,
        city="Lekki",
        phone_number="+2348012345678",
    )
    service._repo.update = AsyncMock(return_value=updated_row)

    result = await service.update(
        str(address_id),
        UserAddressUpdateRequest(city="Lekki"),
        str(user_id),
    )

    assert result.status_code == 200
    update_payload = service._repo.update.await_args.args[2]
    assert update_payload.city == "Lekki"

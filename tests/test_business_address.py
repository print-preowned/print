"""Business address validation and service tests."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.business_address.model import BusinessAddressCreateRequest, BusinessAddressUpdateRequest
from app.business_address.orm import BusinessAddressOrm
from app.business_address.repository import BusinessAddressRepository
from app.business_address.service import BusinessAddressService


def _mock_address_row(**overrides):
    row = MagicMock(spec=BusinessAddressOrm)
    row.id = uuid.uuid4()
    row.business_id = uuid.uuid4()
    row.label = "Main store"
    row.phone_number = None
    row.line1 = "12 Allen Avenue"
    row.line2 = None
    row.city = "Ikeja"
    row.state = "Lagos"
    row.postal_code = None
    row.country_code = "NG"
    row.is_primary = False
    row.pickup_enabled = False
    for key, value in overrides.items():
        setattr(row, key, value)
    return row


@pytest.mark.asyncio
async def test_business_address_create_auto_primary_first_location() -> None:
    business_id = uuid.uuid4()
    session = AsyncMock()
    service = BusinessAddressService(session)
    service._repo = AsyncMock()
    service._repo.count_active_by_business = AsyncMock(return_value=0)
    service._repo.clear_primary_for_business = AsyncMock()
    created_row = _mock_address_row(business_id=business_id, is_primary=True)
    service._repo.create = AsyncMock(return_value=created_row)

    payload = BusinessAddressCreateRequest(
        label="Main store",
        line1="12 Allen Avenue",
        city="Ikeja",
        state="Lagos",
    )

    result = await service.create(payload, str(business_id))

    assert result.status_code == 201
    service._repo.clear_primary_for_business.assert_awaited_once_with(business_id)
    create_arg = service._repo.create.await_args.args[0]
    assert create_arg.is_primary is True
    assert create_arg.business_id == business_id


@pytest.mark.asyncio
async def test_business_address_delete_only_location_is_blocked() -> None:
    business_id = uuid.uuid4()
    address_id = uuid.uuid4()
    session = AsyncMock()
    service = BusinessAddressService(session)
    service._repo = AsyncMock()
    row = MagicMock(spec=BusinessAddressOrm)
    row.is_primary = True
    service._repo.read_by_id = AsyncMock(return_value=row)
    service._repo.count_active_by_business = AsyncMock(return_value=1)

    with pytest.raises(HTTPException) as exc:
        await service.delete(str(address_id), str(business_id))

    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_business_address_set_primary_not_found() -> None:
    service = BusinessAddressService(AsyncMock())
    service._repo = AsyncMock()
    service._repo.set_primary = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.set_primary(str(uuid.uuid4()), str(uuid.uuid4()))

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_business_address_repository_soft_delete() -> None:
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=uuid.uuid4())
    deleted = await BusinessAddressRepository(session).delete(uuid.uuid4(), uuid.uuid4())
    assert deleted is True


@pytest.mark.asyncio
async def test_business_address_update_merges_address_fields() -> None:
    business_id = uuid.uuid4()
    address_id = uuid.uuid4()
    session = AsyncMock()
    service = BusinessAddressService(session)
    service._repo = AsyncMock()

    row = _mock_address_row()
    service._repo.read_by_id = AsyncMock(return_value=row)

    updated_row = _mock_address_row(city="Lekki")
    service._repo.update = AsyncMock(return_value=updated_row)

    result = await service.update(
        str(address_id),
        BusinessAddressUpdateRequest(city="Lekki"),
        str(business_id),
    )

    assert result.status_code == 200
    update_payload = service._repo.update.await_args.args[2]
    assert update_payload.city == "Lekki"


@pytest.mark.asyncio
async def test_business_address_create_enabling_pickup_clears_siblings() -> None:
    business_id = uuid.uuid4()
    session = AsyncMock()
    service = BusinessAddressService(session)
    service._repo = AsyncMock()
    service._repo.count_active_by_business = AsyncMock(return_value=1)
    service._repo.clear_primary_for_business = AsyncMock()
    service._repo.clear_pickup_enabled_for_business = AsyncMock()
    created_row = _mock_address_row(business_id=business_id, pickup_enabled=True)
    service._repo.create = AsyncMock(return_value=created_row)

    payload = BusinessAddressCreateRequest(
        label="Pickup store",
        line1="12 Allen Avenue",
        city="Ikeja",
        state="Lagos",
        pickup_enabled=True,
    )

    await service.create(payload, str(business_id))

    service._repo.clear_pickup_enabled_for_business.assert_awaited_once_with(business_id)


@pytest.mark.asyncio
async def test_business_address_update_enabling_pickup_clears_siblings() -> None:
    business_id = uuid.uuid4()
    address_id = uuid.uuid4()
    session = AsyncMock()
    service = BusinessAddressService(session)
    service._repo = AsyncMock()

    row = _mock_address_row()
    service._repo.read_by_id = AsyncMock(return_value=row)
    service._repo.clear_pickup_enabled_for_business = AsyncMock()
    service._repo.update = AsyncMock(return_value=_mock_address_row(pickup_enabled=True))

    await service.update(
        str(address_id),
        BusinessAddressUpdateRequest(pickup_enabled=True),
        str(business_id),
    )

    service._repo.clear_pickup_enabled_for_business.assert_awaited_once_with(
        business_id,
        exclude_id=address_id,
    )


@pytest.mark.asyncio
async def test_read_pickup_location_for_customer_not_found() -> None:
    business_id = uuid.uuid4()
    service = BusinessAddressService(AsyncMock())
    service._repo = AsyncMock()
    service._repo.read_pickup_location_by_business = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.read_pickup_location_for_customer(str(business_id))

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_read_pickup_location_for_customer_returns_location() -> None:
    business_id = uuid.uuid4()
    service = BusinessAddressService(AsyncMock())
    service._repo = AsyncMock()
    row = _mock_address_row()
    service._repo.read_pickup_location_by_business = AsyncMock(return_value=row)

    result = await service.read_pickup_location_for_customer(str(business_id))

    assert result.status_code == 200
    assert result.data.label == "Main store"

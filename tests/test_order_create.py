"""Order create validation and fulfillment snapshot tests."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.order.model import OrderCreateRequest
from app.order_item.model import OrderItemCreateRequest
from app.order.service import OrderService
from app.utility.address import FULFILLMENT_TYPE_DELIVERY, fulfillment_snapshot_from_user_address


def _address_row(**overrides):
    row = MagicMock()
    row.recipient_name = "Ada Lovelace"
    row.label = "Home"
    row.phone_number = "+2348012345678"
    row.line1 = "12 Allen Avenue"
    row.line2 = None
    row.city = "Ikeja"
    row.state = "Lagos"
    row.postal_code = None
    row.country_code = "NG"
    for key, value in overrides.items():
        setattr(row, key, value)
    return row


class TestFulfillmentSnapshotHelper:
    def test_maps_user_address_to_delivery_snapshot(self) -> None:
        snapshot = fulfillment_snapshot_from_user_address(_address_row())
        assert snapshot["fulfillment_type"] == FULFILLMENT_TYPE_DELIVERY
        assert snapshot["recipient_name"] == "Ada Lovelace"
        assert snapshot["address_label"] == "Home"
        assert snapshot["line1"] == "12 Allen Avenue"
        assert snapshot["city"] == "Ikeja"


@pytest.mark.asyncio
async def test_order_create_snapshots_address_and_seller() -> None:
    user_id = uuid.uuid4()
    business_id = uuid.uuid4()
    address_id = uuid.uuid4()
    order_id = uuid.uuid4()

    session = AsyncMock()
    service = OrderService(session)
    service._repo = AsyncMock()
    service._item_repo = AsyncMock()
    service._variant_repo = AsyncMock()
    service._business_book_repo = AsyncMock()
    service._business_repo = AsyncMock()
    service._user_address_repo = AsyncMock()

    variant_id = uuid.uuid4()
    listing_id = uuid.uuid4()

    variant = MagicMock()
    variant.status = "ACTIVE"
    variant.business_book_id = listing_id
    variant.currency = "NGN"
    variant.stock = 5
    variant.price = Decimal("10.00")
    variant.discount = None

    listing = MagicMock()
    listing.status = "ACTIVE"
    listing.business_id = business_id

    business = MagicMock()
    business.name = "Print Books Lagos"

    address = _address_row()

    order_row = MagicMock()
    order_row.id = order_id
    order_row.user_id = user_id
    order_row.reference = "PRT-1"
    order_row.currency = "NGN"
    order_row.total_amount = Decimal("20.00")
    order_row.status = "PLACED"
    order_row.business_id = business_id
    order_row.business_name = "Print Books Lagos"
    order_row.fulfillment_type = FULFILLMENT_TYPE_DELIVERY
    order_row.recipient_name = address.recipient_name
    order_row.address_label = address.label
    order_row.phone_number = address.phone_number
    order_row.line1 = address.line1
    order_row.line2 = address.line2
    order_row.city = address.city
    order_row.state = address.state
    order_row.postal_code = address.postal_code
    order_row.country_code = address.country_code
    order_row.created_at = MagicMock()
    order_row.updated_at = MagicMock()

    service._variant_repo.read_variant_by_id = AsyncMock(return_value=variant)
    service._business_book_repo.read_business_book_by_id = AsyncMock(return_value=listing)
    service._business_repo.read_by_id = AsyncMock(return_value=business)
    service._user_address_repo.read_by_id = AsyncMock(return_value=address)
    service._repo.create_order = AsyncMock(return_value=order_row)
    service._variant_repo.deduct_stock = AsyncMock(return_value=True)
    service._item_repo.create_order_item = AsyncMock(return_value=MagicMock())
    service._repo.list_customer_order_items = AsyncMock(return_value=[])

    payload = OrderCreateRequest(
        reference="PRT-1",
        total_amount=20.0,
        shipping_address_id=str(address_id),
        items=[
            OrderItemCreateRequest(
                variant_id=str(variant_id),
                quantity=2,
                unit_price=10.0,
            )
        ],
    )

    response = await service.create(payload, str(user_id))

    create_call = service._repo.create_order.await_args.args[0]
    assert create_call.business_id == business_id
    assert create_call.business_name == "Print Books Lagos"
    assert create_call.fulfillment_type == FULFILLMENT_TYPE_DELIVERY
    assert create_call.line1 == "12 Allen Avenue"
    assert create_call.recipient_name == "Ada Lovelace"
    assert response.data.fulfillment_address is not None
    assert response.data.fulfillment_address.city == "Ikeja"
    assert response.data.business_name == "Print Books Lagos"


@pytest.mark.asyncio
async def test_order_create_rejects_foreign_address() -> None:
    user_id = uuid.uuid4()
    business_id = uuid.uuid4()
    address_id = uuid.uuid4()

    session = AsyncMock()
    service = OrderService(session)
    service._repo = AsyncMock()
    service._item_repo = AsyncMock()
    service._variant_repo = AsyncMock()
    service._business_book_repo = AsyncMock()
    service._business_repo = AsyncMock()
    service._user_address_repo = AsyncMock()

    variant_id = uuid.uuid4()
    variant = MagicMock()
    variant.status = "ACTIVE"
    variant.business_book_id = uuid.uuid4()
    variant.currency = "NGN"
    variant.stock = 5
    variant.price = Decimal("10.00")
    variant.discount = None

    listing = MagicMock()
    listing.status = "ACTIVE"
    listing.business_id = business_id

    service._variant_repo.read_variant_by_id = AsyncMock(return_value=variant)
    service._business_book_repo.read_business_book_by_id = AsyncMock(return_value=listing)
    service._business_repo.read_by_id = AsyncMock(return_value=MagicMock(name="Seller"))
    service._user_address_repo.read_by_id = AsyncMock(return_value=None)

    payload = OrderCreateRequest(
        reference="PRT-2",
        total_amount=10.0,
        shipping_address_id=str(address_id),
        items=[
            OrderItemCreateRequest(
                variant_id=str(variant_id),
                quantity=1,
                unit_price=10.0,
            )
        ],
    )

    with pytest.raises(HTTPException) as exc:
        await service.create(payload, str(user_id))
    assert exc.value.status_code == 422
    assert exc.value.detail == "Delivery address not found"


@pytest.mark.asyncio
async def test_order_create_rejects_missing_delivery_address() -> None:
    user_id = uuid.uuid4()
    business_id = uuid.uuid4()
    variant_id = uuid.uuid4()

    session = AsyncMock()
    service = OrderService(session)
    service._variant_repo = AsyncMock()
    service._business_book_repo = AsyncMock()
    service._business_repo = AsyncMock()

    variant = MagicMock()
    variant.status = "ACTIVE"
    variant.business_book_id = uuid.uuid4()
    variant.currency = "NGN"
    variant.stock = 5
    variant.price = Decimal("10.00")
    variant.discount = None

    listing = MagicMock()
    listing.status = "ACTIVE"
    listing.business_id = business_id

    service._variant_repo.read_variant_by_id = AsyncMock(return_value=variant)
    service._business_book_repo.read_business_book_by_id = AsyncMock(return_value=listing)
    service._business_repo.read_by_id = AsyncMock(return_value=MagicMock(name="Seller"))

    payload = OrderCreateRequest(
        reference="PRT-4",
        total_amount=10.0,
        shipping_address_id=None,
        items=[
            OrderItemCreateRequest(
                variant_id=str(variant_id),
                quantity=1,
                unit_price=10.0,
            )
        ],
    )

    with pytest.raises(HTTPException) as exc:
        await service.create(payload, str(user_id))
    assert exc.value.status_code == 422
    assert exc.value.detail == "Delivery address is required"


@pytest.mark.asyncio
async def test_order_create_rejects_mixed_business_cart() -> None:
    user_id = uuid.uuid4()
    variant_a = uuid.uuid4()
    variant_b = uuid.uuid4()

    session = AsyncMock()
    service = OrderService(session)
    service._variant_repo = AsyncMock()
    service._business_book_repo = AsyncMock()

    variant_one = MagicMock()
    variant_one.status = "ACTIVE"
    variant_one.business_book_id = uuid.uuid4()
    variant_one.currency = "NGN"
    variant_one.stock = 5
    variant_one.price = Decimal("10.00")
    variant_one.discount = None

    variant_two = MagicMock()
    variant_two.status = "ACTIVE"
    variant_two.business_book_id = uuid.uuid4()
    variant_two.currency = "NGN"
    variant_two.stock = 5
    variant_two.price = Decimal("12.00")
    variant_two.discount = None

    listing_one = MagicMock()
    listing_one.status = "ACTIVE"
    listing_one.business_id = uuid.uuid4()

    listing_two = MagicMock()
    listing_two.status = "ACTIVE"
    listing_two.business_id = uuid.uuid4()

    async def read_variant(variant_id: uuid.UUID):
        if variant_id == variant_a:
            return variant_one
        if variant_id == variant_b:
            return variant_two
        return None

    async def read_listing(listing_id: uuid.UUID):
        if listing_id == variant_one.business_book_id:
            return listing_one
        if listing_id == variant_two.business_book_id:
            return listing_two
        return None

    service._variant_repo.read_variant_by_id = AsyncMock(side_effect=read_variant)
    service._business_book_repo.read_business_book_by_id = AsyncMock(side_effect=read_listing)

    payload = OrderCreateRequest(
        reference="PRT-3",
        total_amount=22.0,
        shipping_address_id=str(uuid.uuid4()),
        items=[
            OrderItemCreateRequest(
                variant_id=str(variant_a),
                quantity=1,
                unit_price=10.0,
            ),
            OrderItemCreateRequest(
                variant_id=str(variant_b),
                quantity=1,
                unit_price=12.0,
            ),
        ],
    )

    with pytest.raises(HTTPException) as exc:
        await service.create(payload, str(user_id))
    assert exc.value.status_code == 422
    assert exc.value.detail == "All items must be from the same seller"

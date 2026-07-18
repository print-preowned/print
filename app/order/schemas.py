from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.order_item.schemas import OrderItemRead

DEFAULT_ORDER_CURRENCY = "NGN"

ORDER_FULFILLMENT_STATUSES = frozenset(
    {"PLACED", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"}
)
# Legacy rows created before fulfillment statuses used ACTIVE.
LEGACY_ORDER_STATUS_ALIASES = frozenset({"ACTIVE"})


class OrderCreate(BaseModel):
    user_id: uuid.UUID
    reference: str
    currency: str = DEFAULT_ORDER_CURRENCY
    total_amount: Decimal
    status: str = "PLACED"


class OrderUpdate(BaseModel):
    user_id: uuid.UUID | None = None
    reference: str | None = None
    currency: str | None = None
    total_amount: Decimal | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class OrderRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    reference: str
    currency: str
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderDetailRead(OrderRead):
    items: list[OrderItemRead]


class BusinessOrderItemRead(OrderItemRead):
    book_title: str


class BusinessOrderSummaryRead(BaseModel):
    id: uuid.UUID
    reference: str
    currency: str
    status: str
    business_total_amount: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusinessOrderDetailRead(BusinessOrderSummaryRead):
    items: list[BusinessOrderItemRead]

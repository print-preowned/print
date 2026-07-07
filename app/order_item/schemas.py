from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrderItemCreate(BaseModel):
    order_id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    currency: str
    discount_applied: Decimal | None = None


class OrderItemUpdate(BaseModel):
    order_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    quantity: int | None = None
    unit_price: Decimal | None = None
    currency: str | None = None
    discount_applied: Decimal | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class OrderItemRead(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    currency: str
    discount_applied: Decimal | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

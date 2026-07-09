from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class VariantCreate(BaseModel):
    business_book_id: uuid.UUID
    description: str | None = None
    stock: int
    price: Decimal
    currency: str = "USD"
    discount: Decimal | None = None
    sku: str | None = None
    image: str | None = None
    product_option_value_ids: list[uuid.UUID]


class VariantUpdate(BaseModel):
    description: str | None = None
    stock: int | None = None
    price: Decimal | None = None
    currency: str | None = None
    discount: Decimal | None = None
    sku: str | None = None
    image: str | None = None

    model_config = ConfigDict(extra="forbid")


class VariantRead(BaseModel):
    id: uuid.UUID
    business_book_id: uuid.UUID
    description: str | None
    stock: int
    price: Decimal
    currency: str
    discount: Decimal | None
    sku: str | None
    image: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResolvedConfigRead(BaseModel):
    variant_type_id: str
    variant_type_name: str
    variant_option_id: str
    variant_option_value: str


class VariantWithConfigRead(VariantRead):
    config: list[ResolvedConfigRead] = []


class PublicCatalogVariantRead(BaseModel):
    id: str
    business_book_id: str
    book_id: str
    book_title: str
    book_image: str | None = None
    business_id: str
    business_name: str
    price: float
    currency: str
    discount: float | None = None
    stock: int
    image: str | None = None
    config: list[ResolvedConfigRead] = []

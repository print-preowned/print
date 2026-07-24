from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class BusinessAddressCreate(BaseModel):
    business_id: uuid.UUID
    label: str
    phone_number: str | None = None
    line1: str
    line2: str | None = None
    city: str
    state: str
    postal_code: str | None = None
    country_code: str = "NG"
    is_primary: bool = False
    pickup_enabled: bool = False


class BusinessAddressUpdate(BaseModel):
    label: str | None = None
    phone_number: str | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    is_primary: bool | None = None
    pickup_enabled: bool | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class BusinessAddressRead(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    label: str
    phone_number: str | None
    line1: str
    line2: str | None
    city: str
    state: str
    postal_code: str | None
    country_code: str
    is_primary: bool
    pickup_enabled: bool

    model_config = ConfigDict(from_attributes=True)

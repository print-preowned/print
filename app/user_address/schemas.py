from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserAddressCreate(BaseModel):
    user_id: uuid.UUID
    label: str | None = None
    recipient_name: str
    phone_number: str | None = None
    line1: str
    line2: str | None = None
    city: str
    state: str
    postal_code: str | None = None
    country_code: str = "NG"
    is_default: bool = False


class UserAddressUpdate(BaseModel):
    label: str | None = None
    recipient_name: str | None = None
    phone_number: str | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    is_default: bool | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class UserAddressRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    label: str | None
    recipient_name: str
    phone_number: str | None
    line1: str
    line2: str | None
    city: str
    state: str
    postal_code: str | None
    country_code: str
    is_default: bool

    model_config = ConfigDict(from_attributes=True)

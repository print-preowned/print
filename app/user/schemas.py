from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserSignup(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    status: str = "NEW"


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: str | None = None
    country_code: str | None = None
    phone_number: str | None = None
    email: EmailStr
    profile_image: str | None = None
    password: str
    status: str = "ACTIVE"
    role_id: uuid.UUID | None = None


class UserUpdate(BaseModel):
    role_id: uuid.UUID | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    country_code: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    profile_image: str | None = None
    password: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class UserRead(BaseModel):
    id: uuid.UUID
    role_id: uuid.UUID | None
    first_name: str
    last_name: str
    middle_name: str | None
    country_code: str | None
    phone_number: str | None
    email: EmailStr
    profile_image: str | None
    password: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

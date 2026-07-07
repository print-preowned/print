from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuthorCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: str | None = None
    about: str | None = None
    image: str | None = None


class AuthorUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    about: str | None = None
    image: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class AuthorRead(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    middle_name: str | None
    about: str | None
    image: str | None
    followers: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BookCreate(BaseModel):
    title: str
    image: str | None = None
    synopsis: str | None = None


class BookUpdate(BaseModel):
    title: str | None = None
    image: str | None = None
    synopsis: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class BookRead(BaseModel):
    id: uuid.UUID
    title: str
    image: str | None
    synopsis: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

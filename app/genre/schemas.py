from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GenreCreate(BaseModel):
    name: str
    description: str | None = None


class GenreUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class GenreRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


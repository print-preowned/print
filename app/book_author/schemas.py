from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BookAuthorCreate(BaseModel):
    book_id: uuid.UUID
    author_id: uuid.UUID


class BookAuthorUpdate(BaseModel):
    book_id: uuid.UUID | None = None
    author_id: uuid.UUID | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class BookAuthorRead(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    author_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

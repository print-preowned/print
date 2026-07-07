from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BookGenreCreate(BaseModel):
    book_id: uuid.UUID
    genre_id: uuid.UUID


class BookGenreUpdate(BaseModel):
    book_id: uuid.UUID | None = None
    genre_id: uuid.UUID | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class BookGenreRead(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    genre_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

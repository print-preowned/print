from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookRatingCreate(BaseModel):
    book_id: uuid.UUID
    user_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    review: str | None = None


class BookRatingUpdate(BaseModel):
    book_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    review: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class BookRatingRead(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    review: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

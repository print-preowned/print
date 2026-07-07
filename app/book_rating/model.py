from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class BookRating(BaseModel):
    id: str
    book_id: str
    user_id: str
    rating: int
    review: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime






class BookRatingCreateRequest(BaseModel):
    book_id: str
    user_id: str
    rating: int
    review: Optional[str] = None


class BookRatingUpdateRequest(BaseModel):
    book_id: str | None = None
    user_id: str | None = None
    rating: Optional[int] = None
    review: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



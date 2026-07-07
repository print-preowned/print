from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BusinessRating(BaseModel):
    id: str
    business_id: str
    user_id: str
    order_item_id: Optional[str] = None
    rating: int
    review: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class BusinessRatingCreateRequest(BaseModel):
    business_id: str
    user_id: str
    order_item_id: str | None = None
    rating: int
    review: Optional[str] = None


class BusinessRatingUpdateRequest(BaseModel):
    business_id: str | None = None
    user_id: str | None = None
    order_item_id: str | None = None
    rating: Optional[int] = None
    review: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

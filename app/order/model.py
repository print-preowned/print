from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.order_item.model import OrderItemCreateRequest


class Order(BaseModel):
    id: str
    user_id: str
    reference: str
    currency: str
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime


class OrderCreateRequest(BaseModel):
    reference: str
    total_amount: float
    items: list[OrderItemCreateRequest] = Field(min_length=1)


class OrderUpdateRequest(BaseModel):
    user_id: str | None = None
    reference: Optional[str] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

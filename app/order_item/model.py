from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.utility.model import BaseAppModel


class OrderItem(BaseAppModel):
    id: str
    order_id: str
    variant_id: str
    quantity: int
    unit_price: float
    currency: str
    discount_applied: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime


class OrderItemCreateRequest(BaseModel):
    order_id: str
    variant_id: str
    quantity: int
    unit_price: float
    currency: str
    discount_applied: float | None = None


class OrderItemUpdateRequest(BaseModel):
    order_id: str | None = None
    variant_id: str | None = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    currency: Optional[str] = None
    discount_applied: Optional[float] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

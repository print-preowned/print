from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import BaseAppModel, PyObjectId


class OrderItem(BaseAppModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    order_id: PyObjectId
    variant_id: PyObjectId
    quantity: int
    unit_price: float
    currency: str
    discount_applied: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)


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

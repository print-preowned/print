from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class OrderItem(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    order_id: PyObjectId
    inventory_item_id: PyObjectId
    quantity: int
    unit_price: float
    currency: str
    discount_applied: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("order_id")
    def serialize_order_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("inventory_item_id")
    def serialize_inventory_item_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class OrderItemCreateRequest(BaseModel):
    order_id: PyObjectId
    inventory_item_id: PyObjectId
    quantity: int
    unit_price: float
    currency: str
    discount_applied: Optional[float] = None
    status: str = "ACTIVE"


class OrderItemUpdateRequest(BaseModel):
    order_id: Optional[PyObjectId] = None
    inventory_item_id: Optional[PyObjectId] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    currency: Optional[str] = None
    discount_applied: Optional[float] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class InventoryItem(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    business_book_id: PyObjectId
    description: Optional[str] = None
    stock: int
    price: float
    currency: str
    discount: Optional[float] = None
    image: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("business_book_id")
    def serialize_business_book_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class InventoryItemCreateRequest(BaseModel):
    business_book_id: PyObjectId
    description: Optional[str] = None
    stock: int
    price: float
    currency: str
    discount: Optional[float] = None
    image: Optional[str] = None
    status: str = "ACTIVE"


class InventoryItemUpdateRequest(BaseModel):
    business_book_id: Optional[PyObjectId] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    discount: Optional[float] = None
    image: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



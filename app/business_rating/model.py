from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class BusinessRating(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    business_id: PyObjectId
    user_id: PyObjectId
    order_item_id: Optional[PyObjectId] = None
    rating: int
    review: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("business_id")
    def serialize_business_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("user_id")
    def serialize_user_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("order_item_id")
    def serialize_order_item_id(self, v: ObjectId | None, _info):
        return str(v) if v is not None else None

    model_config = ConfigDict(arbitrary_types_allowed=True)


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



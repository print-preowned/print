from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class BookRating(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    book_id: PyObjectId
    user_id: PyObjectId
    rating: int
    review: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("book_id")
    def serialize_book_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("user_id")
    def serialize_user_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


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



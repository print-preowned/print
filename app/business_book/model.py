from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class BusinessBook(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    book_id: PyObjectId
    business_id: PyObjectId
    synopsis: Optional[str] = None
    image: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("book_id")
    def serialize_book_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("business_id")
    def serialize_business_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BusinessBookCreateRequest(BaseModel):
    book_id: PyObjectId
    business_id: Optional[PyObjectId] = None  # Injected by server from token
    synopsis: Optional[str] = None
    image: Optional[str] = None
    status: str = "ACTIVE"


class BusinessBookUpdateRequest(BaseModel):
    book_id: Optional[PyObjectId] = None
    business_id: Optional[PyObjectId] = None
    synopsis: Optional[str] = None
    image: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class BusinessBookWithBook(BusinessBook):
    """Business book with book title (and image) for list display."""
    book_title: Optional[str] = None
    book_image: Optional[str] = None



from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import BaseAppModel, PyObjectId


class BookAuthor(BaseAppModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    book_id: PyObjectId
    author_id: PyObjectId
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("book_id")
    def serialize_book_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("author_id")
    def serialize_author_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BookAuthorCreateRequest(BaseModel):
    book_id: PyObjectId
    author_id: PyObjectId
    status: str = "ACTIVE"


class BookAuthorUpdateRequest(BaseModel):
    book_id: Optional[PyObjectId] = None
    author_id: Optional[PyObjectId] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



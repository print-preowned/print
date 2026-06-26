from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import BaseAppModel, PyObjectId


class BookGenre(BaseAppModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    book_id: PyObjectId
    genre_id: PyObjectId
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("book_id")
    def serialize_book_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("genre_id")
    def serialize_genre_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BookGenreCreateRequest(BaseModel):
    book_id: PyObjectId
    genre_id: PyObjectId
    status: str = "ACTIVE"


class BookGenreUpdateRequest(BaseModel):
    book_id: Optional[PyObjectId] = None
    genre_id: Optional[PyObjectId] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



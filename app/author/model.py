from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
)
from app.utility.model import PyObjectId


class Author(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    about: str
    image: str | None
    followers: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AuthorCreateRequest(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    about: str
    image: str
    status: str = "ACTIVE"


class AuthorUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    about: Optional[str] = None
    image: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

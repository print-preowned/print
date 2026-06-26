from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class Business(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    user_id: PyObjectId
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("user_id")
    def serialize_user_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BusinessCreateRequest(BaseModel):
    user_id: Optional[PyObjectId] = None
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    status: str = "ACTIVE"


class BusinessUpdateRequest(BaseModel):
    user_id: Optional[PyObjectId] = None
    name: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class BusinessCreateResponse(BaseModel):
    token: str



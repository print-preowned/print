from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class BusinessUser(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    business_id: PyObjectId
    user_id: PyObjectId
    role_id: PyObjectId
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

    @field_serializer("role_id")
    def serialize_role_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BusinessUserCreateRequest(BaseModel):
    business_id: PyObjectId
    user_id: PyObjectId
    role_id: PyObjectId
    status: str = "ACTIVE"


class BusinessUserUpdateRequest(BaseModel):
    business_id: Optional[PyObjectId] = None
    user_id: Optional[PyObjectId] = None
    role_id: Optional[PyObjectId] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



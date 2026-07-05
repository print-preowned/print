from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from app.utility.model import PyObjectId


def _coerce_id_to_str(value: object) -> str:
    if isinstance(value, ObjectId):
        return str(value)
    return str(value)


class BusinessUser(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    business_id: PyObjectId
    user_id: str
    role_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator("user_id", "role_id", mode="before")
    @classmethod
    def normalize_user_refs(cls, value: object) -> str:
        return _coerce_id_to_str(value)

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("business_id")
    def serialize_business_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BusinessUserCreateRequest(BaseModel):
    business_id: PyObjectId
    user_id: str
    role_id: str
    status: str = "ACTIVE"


class BusinessUserUpdateRequest(BaseModel):
    business_id: Optional[PyObjectId] = None
    user_id: Optional[PyObjectId] = None
    role_id: Optional[PyObjectId] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



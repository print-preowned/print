from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class VariantConfig(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    variant_option_id: PyObjectId
    variant_id: PyObjectId
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("variant_option_id")
    def serialize_variant_option_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("variant_id")
    def serialize_variant_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class VariantConfigCreateRequest(BaseModel):
    variant_option_id: PyObjectId
    variant_id: PyObjectId
    status: str = "ACTIVE"


class VariantConfigUpdateRequest(BaseModel):
    variant_option_id: Optional[PyObjectId] = None
    variant_id: Optional[PyObjectId] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

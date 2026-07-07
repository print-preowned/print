from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class VariantOption(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    variant_type_id: PyObjectId
    value: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("variant_type_id")
    def serialize_variant_type_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class VariantOptionCreateRequest(BaseModel):
    variant_type_id: str
    value: str
    status: str = "ACTIVE"


class VariantOptionUpdateRequest(BaseModel):
    variant_type_id: Optional[str] = None
    value: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



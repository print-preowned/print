from datetime import datetime
from typing import Literal
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


EntityName = Literal["BUSINESS_RATING", "VARIANT", "BUSINESS_BOOK"]


class EntityImage(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    entity_id: PyObjectId
    entity_name: EntityName
    image: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("entity_id")
    def serialize_entity_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class EntityImageCreateRequest(BaseModel):
    entity_id: PyObjectId
    entity_name: EntityName
    image: str
    status: str = "ACTIVE"


class EntityImageUpdateRequest(BaseModel):
    entity_id: PyObjectId | None = None
    entity_name: EntityName | None = None
    image: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")



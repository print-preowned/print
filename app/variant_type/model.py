from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class VariantType(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime




class VariantTypeCreateRequest(BaseModel):
    name: str
    status: str = "ACTIVE"


class VariantTypeUpdateRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



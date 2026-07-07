from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class VariantConfig(BaseModel):
    id: str
    variant_option_id: str
    variant_id: str
    status: str
    created_at: datetime
    updated_at: datetime






class VariantConfigCreateRequest(BaseModel):
    variant_option_id: str
    variant_id: str
    status: str = "ACTIVE"


class VariantConfigUpdateRequest(BaseModel):
    variant_option_id: Optional[str] = None
    variant_id: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

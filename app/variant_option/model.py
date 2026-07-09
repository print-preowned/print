from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class VariantOption(BaseModel):
    id: str
    variant_type_id: str
    value: str
    status: str
    created_at: datetime
    updated_at: datetime


class VariantOptionCreateRequest(BaseModel):
    variant_type_id: str
    value: str
    status: str = "ACTIVE"


class VariantOptionUpdateRequest(BaseModel):
    variant_type_id: Optional[str] = None
    value: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

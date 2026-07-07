from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductOptionValueCreate(BaseModel):
    product_option_id: uuid.UUID
    value: str


class ProductOptionValueUpdate(BaseModel):
    product_option_id: uuid.UUID | None = None
    value: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class ProductOptionValueRead(BaseModel):
    id: uuid.UUID
    product_option_id: uuid.UUID = Field(serialization_alias="variant_type_id")
    value: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VariantProductOptionValueCreate(BaseModel):
    variant_id: uuid.UUID
    product_option_value_id: uuid.UUID


class VariantProductOptionValueRead(BaseModel):
    id: uuid.UUID
    variant_id: uuid.UUID
    product_option_value_id: uuid.UUID = Field(serialization_alias="variant_option_id")
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class VariantProductOptionValueUpdate(BaseModel):
    status: str | None = None

    model_config = ConfigDict(extra="forbid")

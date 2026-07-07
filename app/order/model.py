from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class Order(BaseModel):
    id: str
    user_id: str
    reference: str
    currency: str
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime





class OrderCreateRequest(BaseModel):
    user_id: str
    reference: str
    currency: str
    total_amount: float


class OrderUpdateRequest(BaseModel):
    user_id: str | None = None
    reference: Optional[str] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



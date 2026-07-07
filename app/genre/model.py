from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class Genre(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime




class GenreCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "ACTIVE"


class GenreUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



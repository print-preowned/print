from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import BaseAppModel


class BookGenre(BaseAppModel):
    id: str
    book_id: str
    genre_id: str
    status: str
    created_at: datetime
    updated_at: datetime






class BookGenreCreateRequest(BaseModel):
    book_id: str
    genre_id: str


class BookGenreUpdateRequest(BaseModel):
    book_id: str | None = None
    genre_id: str | None = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



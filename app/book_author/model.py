from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.utility.model import BaseAppModel


class BookAuthor(BaseAppModel):
    id: str
    book_id: str
    author_id: str
    status: str
    created_at: datetime
    updated_at: datetime


class BookAuthorCreateRequest(BaseModel):
    author_id: str


class BookAuthorUpdateRequest(BaseModel):
    author_id: str | None = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

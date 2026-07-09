from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.utility.model import BaseAppModel


class AuthorRef(BaseModel):
    """Minimal author for book read response."""

    id: str
    name: str


class GenreRef(BaseModel):
    """Minimal genre for book read response."""

    id: str
    name: str


class Book(BaseAppModel):
    id: str
    title: str
    image: str
    synopsis: str
    status: str
    created_at: datetime
    updated_at: datetime


class BookCreateRequest(BaseModel):
    title: str
    synopsis: str
    image: str = ""
    author_ids: list[str] = []
    genre_ids: list[str] = []


class BookUpdateRequest(BaseModel):
    title: Optional[str] = None
    image: Optional[str] = None
    synopsis: Optional[str] = None
    status: Optional[str] = None
    author_ids: Optional[list[str]] = None
    genre_ids: Optional[list[str]] = None


class BookUploadUrlResponse(BaseModel):
    upload_url: str
    url: str


class BookReadResponse(Book):
    """Book with related authors and genres populated."""

    authors: list[AuthorRef] = []
    genres: list[GenreRef] = []

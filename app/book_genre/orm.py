from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class BookGenreOrm(BaseOrm):
    __tablename__ = "book_genres"

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("books.id"),
        nullable=False,
    )
    genre_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("genres.id"),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "uq_book_genres_book_genre_active",
            "book_id",
            "genre_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_book_genres_book_id", "book_id"),
        Index("ix_book_genres_genre_id", "genre_id"),
        Index("ix_book_genres_deleted_at", "deleted_at"),
    )

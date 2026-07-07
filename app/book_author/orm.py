from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class BookAuthorOrm(BaseOrm):
    __tablename__ = "book_authors"

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("books.id"),
        nullable=False,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("authors.id"),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "uq_book_authors_book_author_active",
            "book_id",
            "author_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_book_authors_book_id", "book_id"),
        Index("ix_book_authors_author_id", "author_id"),
        Index("ix_book_authors_deleted_at", "deleted_at"),
    )

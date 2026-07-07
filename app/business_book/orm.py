from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class BusinessBookOrm(BaseOrm):
    __tablename__ = "business_books"

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("books.id"),
        nullable=False,
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("businesses.id"),
        nullable=False,
    )
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    image: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        Index(
            "uq_business_books_business_book_active",
            "business_id",
            "book_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_business_books_business_id_status", "business_id", "status"),
        Index("ix_business_books_deleted_at", "deleted_at"),
    )

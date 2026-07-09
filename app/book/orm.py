from __future__ import annotations

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.utility.orm import BaseOrm


class BookOrm(BaseOrm):
    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_books_deleted_at", "deleted_at"),
        Index("ix_books_status", "status"),
    )

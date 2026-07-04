from __future__ import annotations

from sqlalchemy import Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.utility.orm import Base, SoftDeleteMixin, StatusMixin, TimestampMixin, UUIDPrimaryKeyMixin


class GenreOrm(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, StatusMixin, Base):
    __tablename__ = "genres"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index(
            "uq_genres_name_active",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_genres_deleted_at", "deleted_at"),
    )


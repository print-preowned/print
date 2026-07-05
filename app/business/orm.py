from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class BusinessOrm(BaseOrm):
    __tablename__ = "businesses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        Index(
            "uq_businesses_user_id_active",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_businesses_user_id", "user_id"),
        Index("ix_businesses_deleted_at", "deleted_at"),
    )

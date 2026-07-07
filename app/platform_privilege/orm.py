from __future__ import annotations

from sqlalchemy import Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.utility.orm import BaseOrm


class PlatformPrivilegeOrm(BaseOrm):
    __tablename__ = "platform_privileges"

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index(
            "uq_platform_privileges_code_active",
            "code",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_platform_privileges_deleted_at", "deleted_at"),
        Index("ix_platform_privileges_status", "status"),
    )

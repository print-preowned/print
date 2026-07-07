from __future__ import annotations

from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.utility.orm import BaseOrm


class PlatformPrivilegeSetOrm(BaseOrm):
    __tablename__ = "platform_privilege_sets"

    name: Mapped[str] = mapped_column(String(120), nullable=False)

    __table_args__ = (
        Index(
            "uq_platform_privilege_sets_name_active",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_platform_privilege_sets_deleted_at", "deleted_at"),
        Index("ix_platform_privilege_sets_status", "status"),
    )

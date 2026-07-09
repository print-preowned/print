from __future__ import annotations

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.utility.orm import BaseOrm


class RoleOrm(BaseOrm):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("uq_roles_code", "code", unique=True),
        Index("ix_roles_deleted_at", "deleted_at"),
        Index("ix_roles_status", "status"),
    )

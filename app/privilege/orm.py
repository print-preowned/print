from __future__ import annotations

from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.utility.orm import BaseOrm


class PrivilegeOrm(BaseOrm):
    __tablename__ = "privileges"

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    module_name: Mapped[str] = mapped_column(String(32), nullable=False)

    __table_args__ = (
        Index("uq_privileges_code", "code", unique=True),
        Index("ix_privileges_module_name", "module_name"),
        Index("ix_privileges_deleted_at", "deleted_at"),
    )

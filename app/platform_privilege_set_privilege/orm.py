from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class PlatformPrivilegeSetPrivilegeOrm(BaseOrm):
    __tablename__ = "platform_privilege_set_privileges"

    privilege_set_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("platform_privilege_sets.id"),
        nullable=False,
    )
    privilege_code: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        Index(
            "uq_platform_privilege_set_privileges_set_code_active",
            "privilege_set_id",
            "privilege_code",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_platform_privilege_set_privileges_set_id", "privilege_set_id"),
        Index("ix_platform_privilege_set_privileges_code", "privilege_code"),
        Index("ix_platform_privilege_set_privileges_deleted_at", "deleted_at"),
    )

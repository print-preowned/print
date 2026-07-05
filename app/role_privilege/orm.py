from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class RolePrivilegeOrm(BaseOrm):
    __tablename__ = "role_privileges"

    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=False,
    )
    # Stable authority key; FK to privileges.code deferred until immutability rules are locked.
    privilege_code: Mapped[str] = mapped_column(String(32), nullable=False)

    __table_args__ = (
        Index(
            "uq_role_privileges_role_code_active",
            "role_id",
            "privilege_code",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_role_privileges_role_id", "role_id"),
        Index("ix_role_privileges_privilege_code", "privilege_code"),
        Index("ix_role_privileges_deleted_at", "deleted_at"),
    )

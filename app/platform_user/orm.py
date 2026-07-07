from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class PlatformUserOrm(BaseOrm):
    __tablename__ = "platform_users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    platform_privilege_set_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("platform_privilege_sets.id"),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "uq_platform_users_user_id_active",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_platform_users_privilege_set_id", "platform_privilege_set_id"),
        Index("ix_platform_users_deleted_at", "deleted_at"),
    )

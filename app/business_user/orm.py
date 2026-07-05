from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class BusinessUserOrm(BaseOrm):
    __tablename__ = "business_users"

    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("businesses.id"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "uq_business_users_business_user_active",
            "business_id",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_business_users_user_id", "user_id"),
        Index("ix_business_users_business_id", "business_id"),
        Index("ix_business_users_deleted_at", "deleted_at"),
    )

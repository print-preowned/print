from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class UserOrm(BaseOrm):
    __tablename__ = "users"

    role_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(16), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        Index(
            "uq_users_email_active",
            func.lower(email),
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_users_status", "status"),
        Index("ix_users_deleted_at", "deleted_at"),
        Index("ix_users_role_id", "role_id"),
    )

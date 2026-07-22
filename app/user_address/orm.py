from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.utility.orm import BaseOrm


class UserAddressOrm(BaseOrm):
    __tablename__ = "user_addresses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recipient_name: Mapped[str] = mapped_column(String(64), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(16), nullable=True)
    line1: Mapped[str] = mapped_column(String(128), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, server_default="NG")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    __table_args__ = (
        Index(
            "uq_user_addresses_user_default_active",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND is_default = true"),
        ),
        Index("ix_user_addresses_deleted_at", "deleted_at"),
    )

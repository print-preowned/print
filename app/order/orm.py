from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class OrderOrm(BaseOrm):
    __tablename__ = "orders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    reference: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2), nullable=False)
    business_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("businesses.id"),
        nullable=True,
        index=True,
    )
    business_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fulfillment_type: Mapped[str | None] = mapped_column(String(8), nullable=True)
    recipient_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(16), nullable=True)
    line1: Mapped[str | None] = mapped_column(String(128), nullable=True)
    line2: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str | None] = mapped_column(String(32), nullable=True)
    state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)

    __table_args__ = (
        Index(
            "uq_orders_reference_active",
            "reference",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_orders_user_id_status", "user_id", "status"),
        Index("ix_orders_deleted_at", "deleted_at"),
    )

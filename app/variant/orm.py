from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class VariantOrm(BaseOrm):
    __tablename__ = "variants"

    business_book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("business_books.id"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    discount: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(64), nullable=True)
    image: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        Index("ix_variants_business_book_id_status", "business_book_id", "status"),
        Index("ix_variants_deleted_at", "deleted_at"),
        CheckConstraint("stock >= 0", name="ck_variants_stock_non_negative"),
        CheckConstraint("price >= 0", name="ck_variants_price_non_negative"),
        CheckConstraint(
            "discount IS NULL OR (discount >= 0 AND discount <= 100)",
            name="ck_variants_discount_range",
        ),
    )

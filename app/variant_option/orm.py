from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class ProductOptionValueOrm(BaseOrm):
    __tablename__ = "product_option_values"

    product_option_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("product_options.id"),
        nullable=False,
    )
    value: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        Index(
            "uq_product_option_values_option_value_active",
            "product_option_id",
            "value",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_product_option_values_product_option_id", "product_option_id"),
        Index("ix_product_option_values_deleted_at", "deleted_at"),
    )

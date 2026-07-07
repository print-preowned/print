from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class VariantProductOptionValueOrm(BaseOrm):
    __tablename__ = "variant_product_option_values"

    variant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("variants.id"),
        nullable=False,
    )
    product_option_value_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("product_option_values.id"),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "uq_variant_product_option_values_pair_active",
            "variant_id",
            "product_option_value_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_variant_product_option_values_variant_id", "variant_id"),
        Index("ix_variant_product_option_values_value_id", "product_option_value_id"),
        Index("ix_variant_product_option_values_deleted_at", "deleted_at"),
    )

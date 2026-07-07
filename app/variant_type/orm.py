from __future__ import annotations

from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.utility.orm import BaseOrm


class ProductOptionOrm(BaseOrm):
    __tablename__ = "product_options"

    name: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        Index(
            "uq_product_options_name_active",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_product_options_deleted_at", "deleted_at"),
        Index("ix_product_options_status", "status"),
    )

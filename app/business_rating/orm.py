from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.utility.orm import BaseOrm


class BusinessRatingOrm(BaseOrm):
    __tablename__ = "business_ratings"

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
    order_item_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("order_items.id"),
        nullable=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_business_ratings_rating_range"),
        Index(
            "uq_business_ratings_order_item_active",
            "order_item_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND order_item_id IS NOT NULL"),
        ),
        Index("ix_business_ratings_business_id", "business_id"),
        Index("ix_business_ratings_user_id", "user_id"),
        Index("ix_business_ratings_order_item_id", "order_item_id"),
        Index("ix_business_ratings_deleted_at", "deleted_at"),
    )

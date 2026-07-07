"""create book_ratings and business_ratings tables

Revision ID: 20260707_0011
Revises: 20260707_0010
Create Date: 2026-07-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260707_0011"
down_revision: str | None = "20260707_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BASE_COLUMNS = (
    sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    ),
    sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    ),
    sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("status", sa.String(length=32), server_default="ACTIVE", nullable=False),
)


def upgrade() -> None:
    op.create_table(
        "book_ratings",
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review", sa.Text(), nullable=True),
        *_BASE_COLUMNS,
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name=op.f("ck_book_ratings_rating_range")),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], name=op.f("fk_book_ratings_book_id_books")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_book_ratings_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_book_ratings")),
    )
    op.create_index(
        "uq_book_ratings_book_user_active",
        "book_ratings",
        ["book_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_book_ratings_book_id", "book_ratings", ["book_id"], unique=False)
    op.create_index("ix_book_ratings_user_id", "book_ratings", ["user_id"], unique=False)
    op.create_index("ix_book_ratings_deleted_at", "book_ratings", ["deleted_at"], unique=False)

    op.create_table(
        "business_ratings",
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("order_item_id", sa.Uuid(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review", sa.Text(), nullable=True),
        *_BASE_COLUMNS,
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name=op.f("ck_business_ratings_rating_range")),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name=op.f("fk_business_ratings_business_id_businesses"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_business_ratings_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["order_item_id"],
            ["order_items.id"],
            name=op.f("fk_business_ratings_order_item_id_order_items"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_business_ratings")),
    )
    op.create_index(
        "uq_business_ratings_order_item_active",
        "business_ratings",
        ["order_item_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND order_item_id IS NOT NULL"),
    )
    op.create_index("ix_business_ratings_business_id", "business_ratings", ["business_id"], unique=False)
    op.create_index("ix_business_ratings_user_id", "business_ratings", ["user_id"], unique=False)
    op.create_index("ix_business_ratings_order_item_id", "business_ratings", ["order_item_id"], unique=False)
    op.create_index("ix_business_ratings_deleted_at", "business_ratings", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_business_ratings_deleted_at", table_name="business_ratings")
    op.drop_index("ix_business_ratings_order_item_id", table_name="business_ratings")
    op.drop_index("ix_business_ratings_user_id", table_name="business_ratings")
    op.drop_index("ix_business_ratings_business_id", table_name="business_ratings")
    op.drop_index("uq_business_ratings_order_item_active", table_name="business_ratings")
    op.drop_table("business_ratings")

    op.drop_index("ix_book_ratings_deleted_at", table_name="book_ratings")
    op.drop_index("ix_book_ratings_user_id", table_name="book_ratings")
    op.drop_index("ix_book_ratings_book_id", table_name="book_ratings")
    op.drop_index("uq_book_ratings_book_user_active", table_name="book_ratings")
    op.drop_table("book_ratings")

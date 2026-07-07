"""create marketplace listing and variant tables

Revision ID: 20260707_0007
Revises: 20260707_0006
Create Date: 2026-07-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260707_0007"
down_revision: str | None = "20260707_0006"
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
        "books",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("image", sa.String(length=512), nullable=True),
        sa.Column("synopsis", sa.Text(), nullable=True),
        *_BASE_COLUMNS,
        sa.PrimaryKeyConstraint("id", name=op.f("pk_books")),
    )
    op.create_index("ix_books_deleted_at", "books", ["deleted_at"], unique=False)
    op.create_index("ix_books_status", "books", ["status"], unique=False)

    op.create_table(
        "business_books",
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("image", sa.String(length=512), nullable=True),
        *_BASE_COLUMNS,
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], name=op.f("fk_business_books_book_id_books")),
        sa.ForeignKeyConstraint(
            ["business_id"], ["businesses.id"], name=op.f("fk_business_books_business_id_businesses")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_business_books")),
    )
    op.create_index("ix_business_books_deleted_at", "business_books", ["deleted_at"], unique=False)
    op.create_index(
        "ix_business_books_business_id_status",
        "business_books",
        ["business_id", "status"],
        unique=False,
    )
    op.create_index(
        "uq_business_books_business_book_active",
        "business_books",
        ["business_id", "book_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "variants",
        sa.Column("business_book_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column("discount", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("sku", sa.String(length=64), nullable=True),
        sa.Column("image", sa.String(length=512), nullable=True),
        *_BASE_COLUMNS,
        sa.CheckConstraint("stock >= 0", name=op.f("ck_variants_stock_non_negative")),
        sa.CheckConstraint("price >= 0", name=op.f("ck_variants_price_non_negative")),
        sa.CheckConstraint(
            "discount IS NULL OR (discount >= 0 AND discount <= 100)",
            name=op.f("ck_variants_discount_range"),
        ),
        sa.ForeignKeyConstraint(
            ["business_book_id"],
            ["business_books.id"],
            name=op.f("fk_variants_business_book_id_business_books"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_variants")),
    )
    op.create_index("ix_variants_deleted_at", "variants", ["deleted_at"], unique=False)
    op.create_index(
        "ix_variants_business_book_id_status",
        "variants",
        ["business_book_id", "status"],
        unique=False,
    )

    op.create_table(
        "variant_product_option_values",
        sa.Column("variant_id", sa.Uuid(), nullable=False),
        sa.Column("product_option_value_id", sa.Uuid(), nullable=False),
        *_BASE_COLUMNS,
        sa.ForeignKeyConstraint(
            ["product_option_value_id"],
            ["product_option_values.id"],
            name=op.f(
                "fk_variant_product_option_values_product_option_value_id_product_option_values"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["variants.id"],
            name=op.f("fk_variant_product_option_values_variant_id_variants"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_variant_product_option_values")),
    )
    op.create_index(
        "ix_variant_product_option_values_deleted_at",
        "variant_product_option_values",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_variant_product_option_values_variant_id",
        "variant_product_option_values",
        ["variant_id"],
        unique=False,
    )
    op.create_index(
        "ix_variant_product_option_values_value_id",
        "variant_product_option_values",
        ["product_option_value_id"],
        unique=False,
    )
    op.create_index(
        "uq_variant_product_option_values_pair_active",
        "variant_product_option_values",
        ["variant_id", "product_option_value_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_variant_product_option_values_pair_active",
        table_name="variant_product_option_values",
    )
    op.drop_index(
        "ix_variant_product_option_values_value_id",
        table_name="variant_product_option_values",
    )
    op.drop_index(
        "ix_variant_product_option_values_variant_id",
        table_name="variant_product_option_values",
    )
    op.drop_index(
        "ix_variant_product_option_values_deleted_at",
        table_name="variant_product_option_values",
    )
    op.drop_table("variant_product_option_values")

    op.drop_index("ix_variants_business_book_id_status", table_name="variants")
    op.drop_index("ix_variants_deleted_at", table_name="variants")
    op.drop_table("variants")

    op.drop_index("uq_business_books_business_book_active", table_name="business_books")
    op.drop_index("ix_business_books_business_id_status", table_name="business_books")
    op.drop_index("ix_business_books_deleted_at", table_name="business_books")
    op.drop_table("business_books")

    op.drop_index("ix_books_status", table_name="books")
    op.drop_index("ix_books_deleted_at", table_name="books")
    op.drop_table("books")

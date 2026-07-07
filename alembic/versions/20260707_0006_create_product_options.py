"""create product option catalog tables

Revision ID: 20260707_0006
Revises: 20260707_0005
Create Date: 2026-07-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260707_0006"
down_revision: str | None = "20260707_0005"
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
        "product_options",
        sa.Column("name", sa.String(length=64), nullable=False),
        *_BASE_COLUMNS,
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_options")),
    )
    op.create_index("ix_product_options_deleted_at", "product_options", ["deleted_at"], unique=False)
    op.create_index("ix_product_options_status", "product_options", ["status"], unique=False)
    op.create_index(
        "uq_product_options_name_active",
        "product_options",
        ["name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "product_option_values",
        sa.Column("product_option_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.String(length=64), nullable=False),
        *_BASE_COLUMNS,
        sa.ForeignKeyConstraint(
            ["product_option_id"],
            ["product_options.id"],
            name=op.f("fk_product_option_values_product_option_id_product_options"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_option_values")),
    )
    op.create_index(
        "ix_product_option_values_deleted_at",
        "product_option_values",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_product_option_values_product_option_id",
        "product_option_values",
        ["product_option_id"],
        unique=False,
    )
    op.create_index(
        "uq_product_option_values_option_value_active",
        "product_option_values",
        ["product_option_id", "value"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_product_option_values_option_value_active",
        table_name="product_option_values",
    )
    op.drop_index(
        "ix_product_option_values_product_option_id",
        table_name="product_option_values",
    )
    op.drop_index("ix_product_option_values_deleted_at", table_name="product_option_values")
    op.drop_table("product_option_values")

    op.drop_index("uq_product_options_name_active", table_name="product_options")
    op.drop_index("ix_product_options_status", table_name="product_options")
    op.drop_index("ix_product_options_deleted_at", table_name="product_options")
    op.drop_table("product_options")

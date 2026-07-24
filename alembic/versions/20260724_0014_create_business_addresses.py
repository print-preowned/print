"""create business_addresses table

Revision ID: 20260724_0014
Revises: 20260721_0013
Create Date: 2026-07-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260724_0014"
down_revision: str | None = "20260721_0013"
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
        "business_addresses",
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=32), nullable=False),
        sa.Column("phone_number", sa.String(length=16), nullable=True),
        sa.Column("line1", sa.String(length=128), nullable=False),
        sa.Column("line2", sa.String(length=128), nullable=True),
        sa.Column("city", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("postal_code", sa.String(length=8), nullable=True),
        sa.Column("country_code", sa.String(length=2), server_default="NG", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("pickup_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_BASE_COLUMNS,
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name=op.f("fk_business_addresses_business_id_businesses"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_business_addresses")),
    )
    op.create_index(
        "ix_business_addresses_business_id",
        "business_addresses",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "ix_business_addresses_deleted_at",
        "business_addresses",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "uq_business_addresses_business_primary_active",
        "business_addresses",
        ["business_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND is_primary = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_business_addresses_business_primary_active", table_name="business_addresses")
    op.drop_index("ix_business_addresses_deleted_at", table_name="business_addresses")
    op.drop_index("ix_business_addresses_business_id", table_name="business_addresses")
    op.drop_table("business_addresses")

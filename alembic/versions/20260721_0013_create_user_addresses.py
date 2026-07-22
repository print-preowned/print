"""create user_addresses table

Revision ID: 20260721_0013
Revises: 20260707_0012
Create Date: 2026-07-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260721_0013"
down_revision: str | None = "20260707_0012"
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
        "user_addresses",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=32), nullable=True),
        sa.Column("recipient_name", sa.String(length=64), nullable=False),
        sa.Column("phone_number", sa.String(length=16), nullable=True),
        sa.Column("line1", sa.String(length=128), nullable=False),
        sa.Column("line2", sa.String(length=128), nullable=True),
        sa.Column("city", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("postal_code", sa.String(length=8), nullable=True),
        sa.Column("country_code", sa.String(length=2), server_default="NG", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_BASE_COLUMNS,
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_addresses_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_addresses")),
    )
    op.create_index("ix_user_addresses_user_id", "user_addresses", ["user_id"], unique=False)
    op.create_index("ix_user_addresses_deleted_at", "user_addresses", ["deleted_at"], unique=False)
    op.create_index(
        "uq_user_addresses_user_default_active",
        "user_addresses",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND is_default = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_user_addresses_user_default_active", table_name="user_addresses")
    op.drop_index("ix_user_addresses_deleted_at", table_name="user_addresses")
    op.drop_index("ix_user_addresses_user_id", table_name="user_addresses")
    op.drop_table("user_addresses")

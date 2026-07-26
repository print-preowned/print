"""add order fulfillment address and seller columns

Revision ID: 20260725_0015
Revises: 20260724_0014
Create Date: 2026-07-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260725_0015"
down_revision: str | None = "20260724_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("business_id", sa.Uuid(), nullable=True))
    op.add_column("orders", sa.Column("business_name", sa.String(length=64), nullable=True))
    op.add_column("orders", sa.Column("fulfillment_type", sa.String(length=16), nullable=True))
    op.add_column("orders", sa.Column("recipient_name", sa.String(length=64), nullable=True))
    op.add_column("orders", sa.Column("address_label", sa.String(length=32), nullable=True))
    op.add_column("orders", sa.Column("phone_number", sa.String(length=16), nullable=True))
    op.add_column("orders", sa.Column("line1", sa.String(length=128), nullable=True))
    op.add_column("orders", sa.Column("line2", sa.String(length=128), nullable=True))
    op.add_column("orders", sa.Column("city", sa.String(length=32), nullable=True))
    op.add_column("orders", sa.Column("state", sa.String(length=32), nullable=True))
    op.add_column("orders", sa.Column("postal_code", sa.String(length=8), nullable=True))
    op.add_column("orders", sa.Column("country_code", sa.String(length=2), nullable=True))
    op.create_foreign_key(
        op.f("fk_orders_business_id_businesses"),
        "orders",
        "businesses",
        ["business_id"],
        ["id"],
    )
    op.create_index("ix_orders_business_id", "orders", ["business_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_orders_business_id", table_name="orders")
    op.drop_constraint(op.f("fk_orders_business_id_businesses"), "orders", type_="foreignkey")
    op.drop_column("orders", "country_code")
    op.drop_column("orders", "postal_code")
    op.drop_column("orders", "state")
    op.drop_column("orders", "city")
    op.drop_column("orders", "line2")
    op.drop_column("orders", "line1")
    op.drop_column("orders", "phone_number")
    op.drop_column("orders", "address_label")
    op.drop_column("orders", "recipient_name")
    op.drop_column("orders", "fulfillment_type")
    op.drop_column("orders", "business_name")
    op.drop_column("orders", "business_id")

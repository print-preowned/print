"""tighten users column lengths

Revision ID: 20260705_0003
Revises: 20260705_0002
Create Date: 2026-07-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260705_0003"
down_revision: str | None = "20260705_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "first_name",
        existing_type=sa.String(length=120),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "last_name",
        existing_type=sa.String(length=120),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "middle_name",
        existing_type=sa.String(length=120),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
    op.alter_column(
        "users",
        "phone_number",
        existing_type=sa.String(length=32),
        type_=sa.String(length=16),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "phone_number",
        existing_type=sa.String(length=16),
        type_=sa.String(length=32),
        existing_nullable=True,
    )
    op.alter_column(
        "users",
        "middle_name",
        existing_type=sa.String(length=64),
        type_=sa.String(length=120),
        existing_nullable=True,
    )
    op.alter_column(
        "users",
        "last_name",
        existing_type=sa.String(length=64),
        type_=sa.String(length=120),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "first_name",
        existing_type=sa.String(length=64),
        type_=sa.String(length=120),
        existing_nullable=False,
    )

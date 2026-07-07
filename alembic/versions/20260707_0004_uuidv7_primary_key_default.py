"""set uuidv7() default on primary key columns

Revision ID: 20260707_0004
Revises: 20260705_0003
Create Date: 2026-07-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260707_0004"
down_revision: str | None = "20260705_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "genres",
    "roles",
    "privileges",
    "users",
    "role_privileges",
    "businesses",
    "business_users",
)


def upgrade() -> None:
    for table in _TABLES:
        op.alter_column(
            table,
            "id",
            existing_type=sa.Uuid(),
            server_default=sa.text("uuidv7()"),
            existing_nullable=False,
        )


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.alter_column(
            table,
            "id",
            existing_type=sa.Uuid(),
            server_default=None,
            existing_nullable=False,
        )

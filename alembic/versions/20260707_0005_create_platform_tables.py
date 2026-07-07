"""create platform tables

Revision ID: 20260707_0005
Revises: 20260707_0004
Create Date: 2026-07-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260707_0005"
down_revision: str | None = "20260707_0004"
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
        "platform_privileges",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_BASE_COLUMNS,
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_privileges")),
    )
    op.create_index(
        "ix_platform_privileges_deleted_at",
        "platform_privileges",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_platform_privileges_status",
        "platform_privileges",
        ["status"],
        unique=False,
    )
    op.create_index(
        "uq_platform_privileges_code_active",
        "platform_privileges",
        ["code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "platform_privilege_sets",
        sa.Column("name", sa.String(length=120), nullable=False),
        *_BASE_COLUMNS,
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_privilege_sets")),
    )
    op.create_index(
        "ix_platform_privilege_sets_deleted_at",
        "platform_privilege_sets",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_platform_privilege_sets_status",
        "platform_privilege_sets",
        ["status"],
        unique=False,
    )
    op.create_index(
        "uq_platform_privilege_sets_name_active",
        "platform_privilege_sets",
        ["name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "platform_privilege_set_privileges",
        sa.Column("privilege_set_id", sa.Uuid(), nullable=False),
        sa.Column("privilege_code", sa.String(length=64), nullable=False),
        *_BASE_COLUMNS,
        sa.ForeignKeyConstraint(
            ["privilege_set_id"],
            ["platform_privilege_sets.id"],
            name=op.f(
                "fk_platform_privilege_set_privileges_privilege_set_id_platform_privilege_sets"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_privilege_set_privileges")),
    )
    op.create_index(
        "ix_platform_privilege_set_privileges_deleted_at",
        "platform_privilege_set_privileges",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_platform_privilege_set_privileges_code",
        "platform_privilege_set_privileges",
        ["privilege_code"],
        unique=False,
    )
    op.create_index(
        "ix_platform_privilege_set_privileges_set_id",
        "platform_privilege_set_privileges",
        ["privilege_set_id"],
        unique=False,
    )
    op.create_index(
        "uq_platform_privilege_set_privileges_set_code_active",
        "platform_privilege_set_privileges",
        ["privilege_set_id", "privilege_code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "platform_users",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("platform_privilege_set_id", sa.Uuid(), nullable=False),
        *_BASE_COLUMNS,
        sa.ForeignKeyConstraint(
            ["platform_privilege_set_id"],
            ["platform_privilege_sets.id"],
            name=op.f("fk_platform_users_platform_privilege_set_id_platform_privilege_sets"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_platform_users_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_users")),
    )
    op.create_index(
        "ix_platform_users_deleted_at",
        "platform_users",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_platform_users_privilege_set_id",
        "platform_users",
        ["platform_privilege_set_id"],
        unique=False,
    )
    op.create_index(
        "uq_platform_users_user_id_active",
        "platform_users",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "platform_invites",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("platform_privilege_set_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("invited_by", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["invited_by"],
            ["users.id"],
            name=op.f("fk_platform_invites_invited_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["platform_privilege_set_id"],
            ["platform_privilege_sets.id"],
            name=op.f("fk_platform_invites_platform_privilege_set_id_platform_privilege_sets"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_invites")),
    )
    op.create_index(
        "ix_platform_invites_status_expires_at",
        "platform_invites",
        ["status", "expires_at"],
        unique=False,
    )
    op.create_index(
        "uq_platform_invites_token_hash",
        "platform_invites",
        ["token_hash"],
        unique=True,
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_platform_invites_email_lower "
            "ON platform_invites (lower(email))"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_platform_invites_email_lower"))
    op.drop_index("uq_platform_invites_token_hash", table_name="platform_invites")
    op.drop_index("ix_platform_invites_status_expires_at", table_name="platform_invites")
    op.drop_table("platform_invites")

    op.drop_index("uq_platform_users_user_id_active", table_name="platform_users")
    op.drop_index("ix_platform_users_privilege_set_id", table_name="platform_users")
    op.drop_index("ix_platform_users_deleted_at", table_name="platform_users")
    op.drop_table("platform_users")

    op.drop_index(
        "uq_platform_privilege_set_privileges_set_code_active",
        table_name="platform_privilege_set_privileges",
    )
    op.drop_index(
        "ix_platform_privilege_set_privileges_set_id",
        table_name="platform_privilege_set_privileges",
    )
    op.drop_index(
        "ix_platform_privilege_set_privileges_code",
        table_name="platform_privilege_set_privileges",
    )
    op.drop_index(
        "ix_platform_privilege_set_privileges_deleted_at",
        table_name="platform_privilege_set_privileges",
    )
    op.drop_table("platform_privilege_set_privileges")

    op.drop_index(
        "uq_platform_privilege_sets_name_active",
        table_name="platform_privilege_sets",
    )
    op.drop_index("ix_platform_privilege_sets_status", table_name="platform_privilege_sets")
    op.drop_index("ix_platform_privilege_sets_deleted_at", table_name="platform_privilege_sets")
    op.drop_table("platform_privilege_sets")

    op.drop_index("uq_platform_privileges_code_active", table_name="platform_privileges")
    op.drop_index("ix_platform_privileges_status", table_name="platform_privileges")
    op.drop_index("ix_platform_privileges_deleted_at", table_name="platform_privileges")
    op.drop_table("platform_privileges")

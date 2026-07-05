"""create auth foundation tables

Revision ID: 20260705_0002
Revises: 20260703_0001
Create Date: 2026-07-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260705_0002"
down_revision: str | None = "20260703_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
    )
    op.create_index("ix_roles_deleted_at", "roles", ["deleted_at"], unique=False)
    op.create_index("ix_roles_status", "roles", ["status"], unique=False)
    op.create_index(
        "uq_roles_code_active",
        "roles",
        ["code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "privileges",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("module_name", sa.String(length=64), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_privileges")),
    )
    op.create_index("ix_privileges_deleted_at", "privileges", ["deleted_at"], unique=False)
    op.create_index("ix_privileges_module_name", "privileges", ["module_name"], unique=False)
    op.create_index(
        "uq_privileges_code_active",
        "privileges",
        ["code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "users",
        sa.Column("role_id", sa.Uuid(), nullable=True),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("middle_name", sa.String(length=120), nullable=True),
        sa.Column("country_code", sa.String(length=8), nullable=True),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("profile_image", sa.String(length=512), nullable=True),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("fk_users_role_id_roles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"], unique=False)
    op.create_index("ix_users_role_id", "users", ["role_id"], unique=False)
    op.create_index("ix_users_status", "users", ["status"], unique=False)
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_users_email_active "
            "ON users (lower(email)) "
            "WHERE deleted_at IS NULL"
        )
    )

    op.create_table(
        "role_privileges",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("privilege_code", sa.String(length=64), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name=op.f("fk_role_privileges_role_id_roles")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_privileges")),
    )
    op.create_index(
        "ix_role_privileges_deleted_at", "role_privileges", ["deleted_at"], unique=False
    )
    op.create_index(
        "ix_role_privileges_privilege_code", "role_privileges", ["privilege_code"], unique=False
    )
    op.create_index("ix_role_privileges_role_id", "role_privileges", ["role_id"], unique=False)
    op.create_index(
        "uq_role_privileges_role_code_active",
        "role_privileges",
        ["role_id", "privilege_code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "businesses",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo", sa.String(length=512), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_businesses_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_businesses")),
    )
    op.create_index("ix_businesses_deleted_at", "businesses", ["deleted_at"], unique=False)
    op.create_index("ix_businesses_user_id", "businesses", ["user_id"], unique=False)
    op.create_index(
        "uq_businesses_user_id_active",
        "businesses",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "business_users",
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["business_id"], ["businesses.id"], name=op.f("fk_business_users_business_id_businesses")
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name=op.f("fk_business_users_role_id_roles")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_business_users_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_business_users")),
    )
    op.create_index("ix_business_users_business_id", "business_users", ["business_id"], unique=False)
    op.create_index("ix_business_users_deleted_at", "business_users", ["deleted_at"], unique=False)
    op.create_index("ix_business_users_user_id", "business_users", ["user_id"], unique=False)
    op.create_index(
        "uq_business_users_business_user_active",
        "business_users",
        ["business_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_business_users_business_user_active", table_name="business_users")
    op.drop_index("ix_business_users_user_id", table_name="business_users")
    op.drop_index("ix_business_users_deleted_at", table_name="business_users")
    op.drop_index("ix_business_users_business_id", table_name="business_users")
    op.drop_table("business_users")

    op.drop_index("uq_businesses_user_id_active", table_name="businesses")
    op.drop_index("ix_businesses_user_id", table_name="businesses")
    op.drop_index("ix_businesses_deleted_at", table_name="businesses")
    op.drop_table("businesses")

    op.drop_index("uq_role_privileges_role_code_active", table_name="role_privileges")
    op.drop_index("ix_role_privileges_role_id", table_name="role_privileges")
    op.drop_index("ix_role_privileges_privilege_code", table_name="role_privileges")
    op.drop_index("ix_role_privileges_deleted_at", table_name="role_privileges")
    op.drop_table("role_privileges")

    op.execute(sa.text("DROP INDEX IF EXISTS uq_users_email_active"))
    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_role_id", table_name="users")
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_table("users")

    op.drop_index("uq_privileges_code_active", table_name="privileges")
    op.drop_index("ix_privileges_module_name", table_name="privileges")
    op.drop_index("ix_privileges_deleted_at", table_name="privileges")
    op.drop_table("privileges")

    op.drop_index("uq_roles_code_active", table_name="roles")
    op.drop_index("ix_roles_status", table_name="roles")
    op.drop_index("ix_roles_deleted_at", table_name="roles")
    op.drop_table("roles")

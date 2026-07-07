"""create authors and book_authors tables

Revision ID: 20260707_0008
Revises: 20260707_0007
Create Date: 2026-07-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260707_0008"
down_revision: str | None = "20260707_0007"
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
        "authors",
        sa.Column("first_name", sa.String(length=64), nullable=False),
        sa.Column("last_name", sa.String(length=64), nullable=False),
        sa.Column("middle_name", sa.String(length=64), nullable=True),
        sa.Column("about", sa.Text(), nullable=True),
        sa.Column("image", sa.String(length=512), nullable=True),
        sa.Column("followers", sa.Integer(), server_default="0", nullable=False),
        *_BASE_COLUMNS,
        sa.PrimaryKeyConstraint("id", name=op.f("pk_authors")),
    )
    op.create_index("ix_authors_deleted_at", "authors", ["deleted_at"], unique=False)
    op.create_index("ix_authors_status", "authors", ["status"], unique=False)

    op.create_table(
        "book_authors",
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        *_BASE_COLUMNS,
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["authors.id"],
            name=op.f("fk_book_authors_author_id_authors"),
        ),
        sa.ForeignKeyConstraint(
            ["book_id"],
            ["books.id"],
            name=op.f("fk_book_authors_book_id_books"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_book_authors")),
    )
    op.create_index(
        "uq_book_authors_book_author_active",
        "book_authors",
        ["book_id", "author_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_book_authors_book_id", "book_authors", ["book_id"], unique=False)
    op.create_index("ix_book_authors_author_id", "book_authors", ["author_id"], unique=False)
    op.create_index("ix_book_authors_deleted_at", "book_authors", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_book_authors_deleted_at", table_name="book_authors")
    op.drop_index("ix_book_authors_author_id", table_name="book_authors")
    op.drop_index("ix_book_authors_book_id", table_name="book_authors")
    op.drop_index("uq_book_authors_book_author_active", table_name="book_authors")
    op.drop_table("book_authors")
    op.drop_index("ix_authors_status", table_name="authors")
    op.drop_index("ix_authors_deleted_at", table_name="authors")
    op.drop_table("authors")

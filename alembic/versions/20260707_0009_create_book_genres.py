"""create book_genres table

Revision ID: 20260707_0009
Revises: 20260707_0008
Create Date: 2026-07-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260707_0009"
down_revision: str | None = "20260707_0008"
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
        "book_genres",
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("genre_id", sa.Uuid(), nullable=False),
        *_BASE_COLUMNS,
        sa.ForeignKeyConstraint(
            ["book_id"],
            ["books.id"],
            name=op.f("fk_book_genres_book_id_books"),
        ),
        sa.ForeignKeyConstraint(
            ["genre_id"],
            ["genres.id"],
            name=op.f("fk_book_genres_genre_id_genres"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_book_genres")),
    )
    op.create_index(
        "uq_book_genres_book_genre_active",
        "book_genres",
        ["book_id", "genre_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_book_genres_book_id", "book_genres", ["book_id"], unique=False)
    op.create_index("ix_book_genres_genre_id", "book_genres", ["genre_id"], unique=False)
    op.create_index("ix_book_genres_deleted_at", "book_genres", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_book_genres_deleted_at", table_name="book_genres")
    op.drop_index("ix_book_genres_genre_id", table_name="book_genres")
    op.drop_index("ix_book_genres_book_id", table_name="book_genres")
    op.drop_index("uq_book_genres_book_genre_active", table_name="book_genres")
    op.drop_table("book_genres")

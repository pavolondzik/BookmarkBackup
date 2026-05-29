"""create bookmarks table

Revision ID: 001
Revises:
Create Date: 2026-05-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bookmarks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("url_normalized", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=1024), nullable=False),
        sa.Column("source_browser", sa.String(length=64), nullable=False),
        sa.Column("folder_path", sa.String(length=2048), nullable=False),
        sa.Column("date_added", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_bookmarks_url_normalized",
        "bookmarks",
        ["url_normalized"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_bookmarks_url_normalized", table_name="bookmarks")
    op.drop_table("bookmarks")

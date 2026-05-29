"""add bookmark sort_index

Revision ID: 003
Revises: 002
Create Date: 2026-05-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bookmarks",
        sa.Column("sort_index", sa.Integer(), nullable=False, server_default="0"),
    )

    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY folder_id
                    ORDER BY id
                ) - 1 AS new_index
            FROM bookmarks
        )
        UPDATE bookmarks AS b
        SET sort_index = ranked.new_index
        FROM ranked
        WHERE b.id = ranked.id
        """
    )


def downgrade() -> None:
    op.drop_column("bookmarks", "sort_index")

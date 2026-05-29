"""expand schema for browser exports and folders

Revision ID: 002
Revises: 001
Create Date: 2026-05-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "browsers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("browser_name", sa.String(length=50), nullable=False),
        sa.Column("browser_version", sa.String(length=50), nullable=True),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "browser_exports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_format", sa.String(length=20), nullable=False),
        sa.Column("source_path", sa.String(length=1024), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("browser_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["browser_id"], ["browsers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "folders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("browser_export_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["browser_export_id"], ["browser_exports.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["folders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.drop_index("ix_bookmarks_url_normalized", table_name="bookmarks")
    op.alter_column("bookmarks", "url", new_column_name="href")
    op.alter_column("bookmarks", "url_normalized", new_column_name="href_normalized")

    op.add_column(
        "bookmarks",
        sa.Column("icon_uri", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column("bookmarks", sa.Column("icon", sa.Text(), nullable=True))
    op.add_column(
        "bookmarks",
        sa.Column("date_modified", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("bookmarks", sa.Column("folder_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_bookmarks_folder_id_folders",
        "bookmarks",
        "folders",
        ["folder_id"],
        ["id"],
    )

    op.drop_column("bookmarks", "source_browser")
    op.drop_column("bookmarks", "folder_path")

    op.alter_column("bookmarks", "icon_uri", server_default=None)
    op.create_index(
        "ix_bookmarks_href_normalized",
        "bookmarks",
        ["href_normalized"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_bookmarks_href_normalized", table_name="bookmarks")

    op.add_column(
        "bookmarks",
        sa.Column("folder_path", sa.String(length=2048), nullable=False, server_default=""),
    )
    op.add_column(
        "bookmarks",
        sa.Column(
            "source_browser",
            sa.String(length=64),
            nullable=False,
            server_default="unknown",
        ),
    )

    op.drop_constraint("fk_bookmarks_folder_id_folders", "bookmarks", type_="foreignkey")
    op.drop_column("bookmarks", "folder_id")
    op.drop_column("bookmarks", "date_modified")
    op.drop_column("bookmarks", "icon")
    op.drop_column("bookmarks", "icon_uri")

    op.alter_column("bookmarks", "href", new_column_name="url")
    op.alter_column("bookmarks", "href_normalized", new_column_name="url_normalized")
    op.create_index(
        "ix_bookmarks_url_normalized",
        "bookmarks",
        ["url_normalized"],
        unique=True,
    )

    op.alter_column("bookmarks", "folder_path", server_default=None)
    op.alter_column("bookmarks", "source_browser", server_default=None)

    op.drop_table("folders")
    op.drop_table("browser_exports")
    op.drop_table("browsers")
    op.drop_table("devices")
    op.drop_table("users")

"""Add database connections and synchronized schema metadata.

Revision ID: 0003_phase3
Revises: 0002_phase2
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_phase3"
down_revision: Union[str, None] = "0002_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "database_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id",
            sa.String(36),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.String(36),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("dialect", sa.String(30), nullable=False),
        sa.Column("encrypted_credentials", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_database_connections_organization_id",
        "database_connections",
        ["organization_id"],
    )
    op.create_index(
        "ix_database_connections_workspace_id",
        "database_connections",
        ["workspace_id"],
    )

    op.create_table(
        "database_tables",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "connection_id",
            sa.String(36),
            sa.ForeignKey("database_connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("schema_name", sa.String(120), nullable=False),
        sa.Column("table_name", sa.String(255), nullable=False),
        sa.Column("columns", sa.JSON(), nullable=False),
        sa.Column("foreign_keys", sa.JSON(), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_database_tables_connection_id",
        "database_tables",
        ["connection_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_database_tables_connection_id", table_name="database_tables")
    op.drop_table("database_tables")
    op.drop_index(
        "ix_database_connections_workspace_id",
        table_name="database_connections",
    )
    op.drop_index(
        "ix_database_connections_organization_id",
        table_name="database_connections",
    )
    op.drop_table("database_connections")

"""Add text-to-SQL requests and explicit query approval state.

Revision ID: 0004_phase5_6
Revises: 0003_phase3
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_phase5_6"
down_revision: Union[str, None] = "0003_phase3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "query_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connection_id", sa.String(36), sa.ForeignKey("database_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(50), nullable=False),
        sa.Column("metric", sa.String(100), nullable=True),
        sa.Column("generated_sql", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("clarification", sa.Text(), nullable=True),
        sa.Column("candidate_hash", sa.String(64), nullable=True),
        sa.Column("approved_sql", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_query_requests_organization_id", "query_requests", ["organization_id"])
    op.create_index("ix_query_requests_workspace_id", "query_requests", ["workspace_id"])
    op.create_index("ix_query_requests_connection_id", "query_requests", ["connection_id"])


def downgrade() -> None:
    op.drop_index("ix_query_requests_connection_id", table_name="query_requests")
    op.drop_index("ix_query_requests_workspace_id", table_name="query_requests")
    op.drop_index("ix_query_requests_organization_id", table_name="query_requests")
    op.drop_table("query_requests")

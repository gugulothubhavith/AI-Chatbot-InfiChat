"""Add connector connections, grants and audit.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import app.models.types

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "connector_connections",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("access_token_enc", sa.Text(), nullable=False),
        sa.Column("refresh_token_enc", sa.Text(), nullable=True),
        sa.Column("scopes", app.models.types.JSONB(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("account_label", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # One connection per provider per user: reconnecting updates in place,
        # so revoking cannot leave a live orphan credential nothing lists.
        sa.UniqueConstraint("user_id", "provider", name="uq_connector_user_provider"),
    )
    op.create_index("ix_connector_connections_user", "connector_connections", ["user_id"])

    op.create_table(
        "connector_grants",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("tool", sa.String(length=60), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["connection_id"], ["connector_connections.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_id", "tool", name="uq_connector_grant_conn_tool"),
    )
    op.create_index("ix_connector_grants_connection", "connector_grants", ["connection_id"])

    op.create_table(
        "connector_audit",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", app.models.types.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("tool", sa.String(length=60), nullable=True),
        sa.Column("detail", sa.String(length=400), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        # SET NULL, not CASCADE: revoking a connection must not erase the
        # record of what was done with it.
        sa.ForeignKeyConstraint(
            ["connection_id"], ["connector_connections.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_connector_audit_user_created", "connector_audit", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_connector_audit_user_created", table_name="connector_audit")
    op.drop_table("connector_audit")
    op.drop_index("ix_connector_grants_connection", table_name="connector_grants")
    op.drop_table("connector_grants")
    op.drop_index("ix_connector_connections_user", table_name="connector_connections")
    op.drop_table("connector_connections")

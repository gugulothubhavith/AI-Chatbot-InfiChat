"""add projects and user_reports

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-09 00:00:00.000000

Two user-facing tables that had no home in the existing schema.

`projects` is user-scoped, unlike `workspaces` (which is org-scoped and owns a
RAG collection). `chat_sessions.project_id` is nullable with ON DELETE SET
NULL, so deleting a project un-files its chats instead of deleting them.

`user_reports` is separate from `incident_tickets`, which models platform
operations and carries no reporter. Its `user_id` is ON DELETE SET NULL so an
account erasure does not destroy an open abuse report or complaint — the row
survives without the identity.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import app.models.types

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column("instructions", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])
    op.create_index("ix_projects_user_created", "projects", ["user_id", "created_at"])

    # Added as a plain nullable column so the migration does not rewrite
    # existing chat_sessions rows.
    op.add_column(
        "chat_sessions",
        sa.Column("project_id", app.models.types.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_chat_sessions_project_id", "chat_sessions", ["project_id"])
    op.create_foreign_key(
        "fk_chat_sessions_project_id",
        "chat_sessions",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Enums are created as plain VARCHAR + CHECK by SQLAlchemy's generic Enum on
    # SQLite and as native types on Postgres; `sa.Enum` handles both.
    op.create_table(
        "user_reports",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", app.models.types.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_email", sa.String(), nullable=True),
        sa.Column(
            "category",
            sa.Enum("BUG", "COMPLAINT", "ABUSE", "BILLING", "FEATURE", "OTHER", name="reportcategory"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED", name="reportstatus"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("diagnostics", app.models.types.JSONB(), nullable=True),
        sa.Column("admin_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_reports_user_id", "user_reports", ["user_id"])
    op.create_index("ix_user_reports_category", "user_reports", ["category"])
    op.create_index("ix_user_reports_status", "user_reports", ["status"])
    op.create_index("ix_user_reports_status_created", "user_reports", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_user_reports_status_created", table_name="user_reports")
    op.drop_index("ix_user_reports_status", table_name="user_reports")
    op.drop_index("ix_user_reports_category", table_name="user_reports")
    op.drop_index("ix_user_reports_user_id", table_name="user_reports")
    op.drop_table("user_reports")
    sa.Enum(name="reportcategory").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reportstatus").drop(op.get_bind(), checkfirst=True)

    op.drop_constraint("fk_chat_sessions_project_id", "chat_sessions", type_="foreignkey")
    op.drop_index("ix_chat_sessions_project_id", table_name="chat_sessions")
    op.drop_column("chat_sessions", "project_id")

    op.drop_index("ix_projects_user_created", table_name="projects")
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_table("projects")

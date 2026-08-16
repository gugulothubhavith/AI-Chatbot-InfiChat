"""Projects: knowledge base, pinned model, scoped memory.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1

`memory_scope` defaults to PROJECT for *new* rows but existing projects are
backfilled to GLOBAL. A project created before this migration has been feeding
its conversations the account's general memories all along; silently narrowing
that on upgrade would make an assistant that knew things yesterday forget them
today, with nothing in the UI to explain why. New projects get the private
default; existing ones keep the behaviour they already had, and the setting is
one switch away in either direction.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import app.models.types

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "projects",
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("projects", sa.Column("default_model", sa.String(), nullable=True))
    op.add_column(
        "projects",
        sa.Column("memory_scope", sa.String(length=20), nullable=False, server_default="PROJECT"),
    )
    op.add_column(
        "projects",
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("projects", sa.Column("knowledge_updated_at", sa.DateTime(), nullable=True))

    # See the module docstring: pre-existing projects keep the behaviour they
    # already had rather than being narrowed underneath their owner.
    op.execute("UPDATE projects SET memory_scope = 'GLOBAL'")

    op.create_table(
        "project_files",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="INDEXED"),
        sa.Column("error", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_project_files_project_id", "project_files", ["project_id"])
    op.create_index("ix_project_files_user_id", "project_files", ["user_id"])
    # Re-uploading a name replaces rather than duplicates: two documents called
    # "brief.pdf" in one knowledge base is a retrieval problem, not a feature.
    op.create_index(
        "ix_project_files_project_name", "project_files", ["project_id", "filename"], unique=True
    )

    # ── Memory scoping ───────────────────────────────────────────────
    op.add_column(
        "memories", sa.Column("project_id", app.models.types.UUID(as_uuid=True), nullable=True)
    )
    op.create_index("ix_memories_project_id", "memories", ["project_id"])
    op.create_index("ix_memories_user_project", "memories", ["user_id", "project_id"])
    # Named, so SQLite — which can only drop a constraint it can name — can
    # reverse this. An anonymous FK would make the downgrade one-way there.
    with op.batch_alter_table("memories") as batch:
        batch.create_foreign_key(
            "fk_memories_project", "projects", ["project_id"], ["id"], ondelete="SET NULL"
        )


def downgrade() -> None:
    with op.batch_alter_table("memories") as batch:
        batch.drop_constraint("fk_memories_project", type_="foreignkey")
    op.drop_index("ix_memories_user_project", table_name="memories")
    op.drop_index("ix_memories_project_id", table_name="memories")
    op.drop_column("memories", "project_id")

    op.drop_index("ix_project_files_project_name", table_name="project_files")
    op.drop_index("ix_project_files_user_id", table_name="project_files")
    op.drop_index("ix_project_files_project_id", table_name="project_files")
    op.drop_table("project_files")

    op.drop_column("projects", "knowledge_updated_at")
    op.drop_column("projects", "file_count")
    op.drop_column("projects", "memory_scope")
    op.drop_column("projects", "default_model")
    op.drop_column("projects", "is_archived")
    op.drop_column("projects", "is_pinned")

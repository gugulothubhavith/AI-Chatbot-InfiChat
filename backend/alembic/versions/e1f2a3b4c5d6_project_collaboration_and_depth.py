"""Project sharing, audit, tags, tool policy and image knowledge.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5

Phases D and E in one revision, because they land together and splitting them
would produce two migrations that are never applied apart.

Three new tables and one existing one extended:

* `project_members`  — who may use a project, and at what rank.
* `project_invites`  — share links, each independently revocable.
* `project_events`   — the activity log. Holds no content, by design.
* `project_tags`     — labels, normalised, one row per tag per project.

`projects` gains `tool_policy`, `allowed_connectors` and `template_id`;
`project_files` gains `uploaded_by_id`, `kind`, `thumbnail` and `read_method`.

**No backfill.** Ownership is derived from `projects.user_id` rather than
represented as an OWNER row in `project_members`, so this migration adds no
membership rows and every existing project keeps working with an empty members
table. That is deliberate: a half-applied backfill of an access-control table
locks people out of their own work, and the only way to be sure it cannot
happen is not to need one.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    # ── D1: membership ────────────────────────────────────────────────
    op.create_table(
        "project_members",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "project_id",
            UUID,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False, server_default="VIEWER"),
        # SET NULL: the person who issued an invitation deleting their account
        # must not revoke everyone else's access.
        sa.Column(
            "invited_by",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])
    op.create_index("ix_project_members_user", "project_members", ["user_id"])

    op.create_table(
        "project_invites",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "project_id",
            UUID,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column(
            "created_by",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("role", sa.String(20), nullable=False, server_default="VIEWER"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_project_invites_project_id", "project_invites", ["project_id"])
    op.create_index("ix_project_invites_token", "project_invites", ["token"])
    op.create_index("ix_project_invites_project", "project_invites", ["project_id"])

    # ── D2: the activity log ──────────────────────────────────────────
    op.create_table(
        "project_events",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "project_id",
            UUID,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # SET NULL with the name kept alongside, so a line read months later
        # still says who did something after they delete their account.
        sa.Column(
            "actor_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_name", sa.String(120), nullable=True),
        sa.Column("action", sa.String(60), nullable=False),
        # Bounded, so this column can never grow into a content store.
        sa.Column("detail", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_project_events_project_id", "project_events", ["project_id"])
    op.create_index(
        "ix_project_events_project_created", "project_events", ["project_id", "created_at"]
    )

    # ── E2: tags ──────────────────────────────────────────────────────
    op.create_table(
        "project_tags",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "project_id",
            UUID,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tag", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", "tag", name="uq_project_tag"),
    )
    op.create_index("ix_project_tags_project_id", "project_tags", ["project_id"])
    op.create_index("ix_project_tags_user_id", "project_tags", ["user_id"])
    # The facet query: this user's tags, grouped and counted.
    op.create_index("ix_project_tags_user_tag", "project_tags", ["user_id", "tag"])

    # ── E1 / E4: project columns ──────────────────────────────────────
    op.add_column(
        "projects",
        sa.Column("tool_policy", sa.String(20), nullable=False, server_default="INHERIT"),
    )
    op.add_column("projects", sa.Column("allowed_connectors", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("template_id", sa.String(60), nullable=True))

    # ── E3 / D1: file columns ─────────────────────────────────────────
    op.add_column(
        "project_files",
        sa.Column(
            "uploaded_by_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "project_files",
        sa.Column("kind", sa.String(20), nullable=False, server_default="DOCUMENT"),
    )
    op.add_column("project_files", sa.Column("thumbnail", sa.Text(), nullable=True))
    op.add_column("project_files", sa.Column("read_method", sa.String(40), nullable=True))


def downgrade() -> None:
    op.drop_column("project_files", "read_method")
    op.drop_column("project_files", "thumbnail")
    op.drop_column("project_files", "kind")
    op.drop_column("project_files", "uploaded_by_id")

    op.drop_column("projects", "template_id")
    op.drop_column("projects", "allowed_connectors")
    op.drop_column("projects", "tool_policy")

    op.drop_table("project_tags")
    op.drop_table("project_events")
    op.drop_table("project_invites")
    op.drop_table("project_members")

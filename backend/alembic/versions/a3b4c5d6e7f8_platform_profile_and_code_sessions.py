"""Platform profile and code-session persistence.

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7

Two tables' worth of things that were never written down anywhere.

**`platform_profile`** (+ its audit table) holds the operator's legal identity —
entity name, registered address, jurisdiction, retention periods, DPO contact,
sub-processor DPA references. These were 140 literal `[PLACEHOLDER: ...]`
markers embedded in four legal markdown documents, which meant they could only
be changed by editing and redeploying the frontend, and the same address could
be stated three different ways across three documents without anything noticing.
A singleton row with a fixed primary key, because two rows means the Privacy
Policy and the invoice can name different companies.

**`code_sessions` / `code_messages`** back the code agent's history. It had no
persistence at all — not a table, not even the `persist` middleware the chat
store uses — so every reload emptied the sidebar's Code History tab. The tab
sitting next to a working Chat History tab is why this read as broken rather
than absent.

Reversible. `downgrade()` drops all four tables; the profile values are lost
with them, which is why `platform_profile_audit` exists — a rollback is
recoverable from a backup of that table alone.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB


def upgrade() -> None:
    # ── Platform profile ──────────────────────────────────────────────
    op.create_table(
        "platform_profile",
        # Integer, not UUID, and always 1. A UUID key invites a second row.
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("values", JSONB, nullable=False, server_default="{}"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        # SET NULL: an admin deleting their own account must not take the
        # company's legal identity with them.
        sa.Column(
            "updated_by_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("updated_by_email", sa.String(320), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "platform_profile_audit",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        # The values as they were *before* the save that produced this row.
        sa.Column("values", JSONB, nullable=False, server_default="{}"),
        sa.Column("changed_keys", JSONB, nullable=False, server_default="[]"),
        sa.Column(
            "changed_by_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("changed_by_email", sa.String(320), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_platform_profile_audit_revision", "platform_profile_audit", ["revision"])
    op.create_index("ix_platform_profile_audit_created_at", "platform_profile_audit", ["created_at"])

    # No seed row. `platform_profile.get_profile()` creates it read-through on
    # first access, and doing it there rather than here means a database
    # restored from an older dump behaves identically to a fresh one.

    # ── Code sessions ─────────────────────────────────────────────────
    op.create_table(
        "code_sessions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "user_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False, server_default="New session"),
        # SET NULL, matching chat_sessions.project_id: deleting a project
        # un-files its sessions rather than deleting the work in them.
        sa.Column(
            "project_id",
            UUID,
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("language", sa.String(40), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_code_sessions_user_id", "code_sessions", ["user_id"])
    op.create_index("ix_code_sessions_project_id", "code_sessions", ["project_id"])
    op.create_index("ix_code_sessions_is_archived", "code_sessions", ["is_archived"])
    # The sidebar query, exactly: one user's live sessions, most recently
    # touched first.
    op.create_index(
        "ix_code_sessions_user_updated",
        "code_sessions",
        ["user_id", "is_archived", "updated_at"],
    )

    op.create_table(
        "code_messages",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "session_id",
            UUID,
            sa.ForeignKey("code_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Explicit ordinal. Two messages written in one transaction can share a
        # timestamp to the microsecond, and then the transcript renders the
        # answer above the question.
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("role", sa.String(20), nullable=False),
        # Text, not String(n): Fernet-encrypted at the ORM layer, and ciphertext
        # is longer than the plaintext it holds.
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("plan", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_code_messages_session_id", "code_messages", ["session_id"])
    op.create_index(
        "ix_code_messages_session_sequence", "code_messages", ["session_id", "sequence"]
    )


def downgrade() -> None:
    op.drop_index("ix_code_messages_session_sequence", table_name="code_messages")
    op.drop_index("ix_code_messages_session_id", table_name="code_messages")
    op.drop_table("code_messages")

    op.drop_index("ix_code_sessions_user_updated", table_name="code_sessions")
    op.drop_index("ix_code_sessions_is_archived", table_name="code_sessions")
    op.drop_index("ix_code_sessions_project_id", table_name="code_sessions")
    op.drop_index("ix_code_sessions_user_id", table_name="code_sessions")
    op.drop_table("code_sessions")

    op.drop_index("ix_platform_profile_audit_created_at", table_name="platform_profile_audit")
    op.drop_index("ix_platform_profile_audit_revision", table_name="platform_profile_audit")
    op.drop_table("platform_profile_audit")
    op.drop_table("platform_profile")

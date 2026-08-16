"""Safety escalations — flagged content held for review and official reporting.

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d6e7f8a9b0c1"
down_revision: Union[str, None] = "c5d6e7f8a9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "safety_escalations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # SET NULL, not CASCADE: deleting the account must not destroy evidence
        # that may be the subject of an active report to an authority.
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("user_snapshot", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("detector", sa.String(length=120), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("matched_terms", postgresql.JSONB(), nullable=False, server_default="[]"),
        # Stored readable on purpose. chat_messages.content is EncryptedText and
        # therefore unusable at the moment a human needs to act on it.
        sa.Column("content_excerpt", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("conversation_context", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="NEW"),
        sa.Column("reviewed_by_email", sa.String(length=320), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reported_to_authority", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("authority_name", sa.String(length=200), nullable=True),
        sa.Column("authority_reference", sa.String(length=200), nullable=True),
        sa.Column("reported_at", sa.DateTime(), nullable=True),
        sa.Column("reported_by_email", sa.String(length=320), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index("ix_safety_escalations_user_id", "safety_escalations", ["user_id"])
    op.create_index("ix_safety_escalations_category", "safety_escalations", ["category"])
    op.create_index("ix_safety_escalations_severity", "safety_escalations", ["severity"])
    op.create_index("ix_safety_escalations_status", "safety_escalations", ["status"])
    op.create_index("ix_safety_escalations_created_at", "safety_escalations", ["created_at"])
    op.create_index("ix_safety_escalations_content_sha256", "safety_escalations", ["content_sha256"])
    # The queue is read as "unhandled, worst first, newest first".
    op.create_index(
        "ix_safety_escalations_status_severity",
        "safety_escalations",
        ["status", "severity", "created_at"],
    )
    # "Has this account been flagged before" decides whether one incident is a
    # pattern, and every reviewer asks it.
    op.create_index(
        "ix_safety_escalations_user_created", "safety_escalations", ["user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_table("safety_escalations")

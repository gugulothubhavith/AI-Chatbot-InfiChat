"""Add group conversations, members and messages.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import app.models.types

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group_conversations",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_by", app.models.types.UUID(as_uuid=True), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("ai_respond_on_mention_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        # SET NULL: the room outlives whoever opened it.
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_group_conversations_created", "group_conversations", ["created_at"])

    op.create_table(
        "group_members",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="MEMBER"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["group_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # One membership per person per room, or role changes become ambiguous.
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_member"),
    )
    op.create_index("ix_group_members_group_user", "group_members", ["group_id", "user_id"])

    op.create_table(
        "group_messages",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", app.models.types.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("author_name", sa.String(length=120), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["group_conversations.id"], ondelete="CASCADE"),
        # SET NULL so an erased account leaves the transcript readable rather
        # than punching holes that change what the conversation meant.
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_group_messages_group_created", "group_messages", ["group_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_group_messages_group_created", table_name="group_messages")
    op.drop_table("group_messages")
    op.drop_index("ix_group_members_group_user", table_name="group_members")
    op.drop_table("group_members")
    op.drop_index("ix_group_conversations_created", table_name="group_conversations")
    op.drop_table("group_conversations")

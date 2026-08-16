"""Group chats: reactions, replies, edits, invite links and AI modes.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0

Every added column is nullable or carries a server default, so this applies to
a live table without rewriting existing rows. `ai_mode` is deliberately *not*
backfilled from `ai_respond_on_mention_only`: the two are reconciled in code
(`group_service.effective_ai_mode`), which means a rollback to the previous
build still honours how each room was configured.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import app.models.types

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Rooms ────────────────────────────────────────────────────────
    op.add_column("group_conversations", sa.Column("color", sa.String(length=20), nullable=True))
    op.add_column(
        "group_conversations",
        sa.Column("ai_mode", sa.String(length=20), nullable=False, server_default="MENTION"),
    )
    op.add_column("group_conversations", sa.Column("ai_model", sa.String(length=120), nullable=True))
    op.add_column(
        "group_conversations",
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "group_conversations", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)
    )
    # Sorting the room list by activity is meaningless while every row is NULL,
    # and NULLs sort unpredictably across backends. Seeded from creation time.
    op.execute("UPDATE group_conversations SET updated_at = created_at WHERE updated_at IS NULL")

    # ── Membership ───────────────────────────────────────────────────
    op.add_column(
        "group_members",
        sa.Column("is_muted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # ── Messages ─────────────────────────────────────────────────────
    op.add_column(
        "group_messages", sa.Column("reply_to_id", app.models.types.UUID(as_uuid=True), nullable=True)
    )
    op.add_column("group_messages", sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("group_messages", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("group_messages", sa.Column("client_id", sa.String(length=64), nullable=True))
    op.create_index("ix_group_messages_reply_to", "group_messages", ["reply_to_id"])
    # A named FK, because SQLite can only drop a constraint it can name — an
    # anonymous one makes this migration one-way on the dev backend.
    with op.batch_alter_table("group_messages") as batch:
        batch.create_foreign_key(
            "fk_group_messages_reply_to",
            "group_messages",
            ["reply_to_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # ── Reactions ────────────────────────────────────────────────────
    op.create_table(
        "group_message_reactions",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("emoji", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["message_id"], ["group_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["group_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # Reacting twice with the same emoji is a toggle, not a second vote.
        sa.UniqueConstraint("message_id", "user_id", "emoji", name="uq_group_reaction"),
    )
    op.create_index("ix_group_reactions_message", "group_message_reactions", ["message_id"])
    op.create_index("ix_group_message_reactions_group", "group_message_reactions", ["group_id"])

    # ── Invite links ─────────────────────────────────────────────────
    op.create_table(
        "group_invites",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("created_by", app.models.types.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="MEMBER"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["group_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_group_invite_token"),
    )
    op.create_index("ix_group_invites_group", "group_invites", ["group_id"])
    op.create_index("ix_group_invites_token", "group_invites", ["token"])


def downgrade() -> None:
    op.drop_index("ix_group_invites_token", table_name="group_invites")
    op.drop_index("ix_group_invites_group", table_name="group_invites")
    op.drop_table("group_invites")

    op.drop_index("ix_group_message_reactions_group", table_name="group_message_reactions")
    op.drop_index("ix_group_reactions_message", table_name="group_message_reactions")
    op.drop_table("group_message_reactions")

    with op.batch_alter_table("group_messages") as batch:
        batch.drop_constraint("fk_group_messages_reply_to", type_="foreignkey")
    op.drop_index("ix_group_messages_reply_to", table_name="group_messages")
    op.drop_column("group_messages", "client_id")
    op.drop_column("group_messages", "deleted_at")
    op.drop_column("group_messages", "edited_at")
    op.drop_column("group_messages", "reply_to_id")

    op.drop_column("group_members", "is_muted")

    op.drop_column("group_conversations", "updated_at")
    op.drop_column("group_conversations", "is_archived")
    op.drop_column("group_conversations", "ai_model")
    op.drop_column("group_conversations", "ai_mode")
    op.drop_column("group_conversations", "color")

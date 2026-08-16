"""Parental controls: guardian links, supervision policy, activity.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2

All three tables are new, so this adds no risk to existing rows. Nothing is
supervised until a guardian invites and the account accepts, so applying the
migration changes no behaviour for anyone.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import app.models.types

revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guardian_links",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("guardian_id", app.models.types.UUID(as_uuid=True), nullable=False),
        # Null until accepted: the invitation names an email, and the account
        # behind it is only known once someone signed in and said yes.
        sa.Column("child_id", app.models.types.UUID(as_uuid=True), nullable=True),
        sa.Column("child_email", sa.String(length=254), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("guardian_label", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["guardian_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_guardian_link_token"),
        # One link per pair, so revoking one cannot leave a second live.
        sa.UniqueConstraint("guardian_id", "child_email", name="uq_guardian_child_email"),
    )
    op.create_index("ix_guardian_links_guardian_id", "guardian_links", ["guardian_id"])
    op.create_index("ix_guardian_links_child_id", "guardian_links", ["child_id"])
    op.create_index("ix_guardian_links_token", "guardian_links", ["token"])
    op.create_index("ix_guardian_links_child_status", "guardian_links", ["child_id", "status"])

    op.create_table(
        "supervision_policies",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("child_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("content_filter", sa.String(length=20), nullable=False, server_default="STANDARD"),
        # Null means no limit. Zero would mean "no usage at all", which is a
        # very different setting; keeping them distinct is what stops a slider
        # at its left edge locking a child out of their account.
        sa.Column("daily_minutes", sa.Integer(), nullable=True),
        sa.Column("quiet_hours_start", sa.Integer(), nullable=True),
        sa.Column("quiet_hours_end", sa.Integer(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("allow_image_generation", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_web_search", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_connectors", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_group_chats", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_incognito", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("blocked_keywords", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", app.models.types.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["child_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        # One policy per child: two guardians must not be able to hold
        # contradictory rules, or enforcement picks one at random.
        sa.UniqueConstraint("child_id", name="uq_supervision_policy_child"),
    )
    op.create_index("ix_supervision_policies_child_id", "supervision_policies", ["child_id"])

    op.create_table(
        "supervision_activity",
        sa.Column("id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("child_id", app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("minutes_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked_count", sa.Integer(), nullable=False, server_default="0"),
        # A tally, never examples. There is deliberately no column here that can
        # hold message text — see the model docstring.
        sa.Column("blocked_categories", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["child_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("child_id", "day", name="uq_supervision_activity_day"),
    )
    op.create_index("ix_supervision_activity_child_id", "supervision_activity", ["child_id"])
    op.create_index(
        "ix_supervision_activity_child_day", "supervision_activity", ["child_id", "day"]
    )


def downgrade() -> None:
    op.drop_index("ix_supervision_activity_child_day", table_name="supervision_activity")
    op.drop_index("ix_supervision_activity_child_id", table_name="supervision_activity")
    op.drop_table("supervision_activity")

    op.drop_index("ix_supervision_policies_child_id", table_name="supervision_policies")
    op.drop_table("supervision_policies")

    op.drop_index("ix_guardian_links_child_status", table_name="guardian_links")
    op.drop_index("ix_guardian_links_token", table_name="guardian_links")
    op.drop_index("ix_guardian_links_child_id", table_name="guardian_links")
    op.drop_index("ix_guardian_links_guardian_id", table_name="guardian_links")
    op.drop_table("guardian_links")

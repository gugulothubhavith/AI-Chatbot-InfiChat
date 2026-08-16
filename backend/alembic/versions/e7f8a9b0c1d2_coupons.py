"""Discount coupons and their redemption ledger.

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-08-13

Two tables rather than a counter on the coupon: `coupons` holds the offer,
`coupon_redemptions` is an append-only record of each use. The counter on
`coupons` is a denormalised convenience for list rendering and is rebuildable
from the ledger — see `coupon_service.recount`.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, None] = "d6e7f8a9b0c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    discount_type = postgresql.ENUM("PERCENT", "FIXED", name="discounttype", create_type=False)
    discount_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "coupons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.Column("discount_type", discount_type, nullable=False, server_default="PERCENT"),
        sa.Column("discount_value", sa.Integer(), nullable=False),
        sa.Column("max_discount_amount", sa.Integer(), nullable=True),
        sa.Column("min_order_amount", sa.Integer(), nullable=True),
        sa.Column("applicable_plan_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("max_redemptions_per_user", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("redemption_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_from", sa.DateTime(), nullable=True),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("new_customers_only", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    # Unique because the code is the identifier a customer types; two coupons
    # answering to one string is not a state the redeem path can resolve.
    op.create_index("ix_coupons_code", "coupons", ["code"], unique=True)

    op.create_table(
        "coupon_redemptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("coupon_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("final_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("billing_cycle", sa.String(length=16), nullable=True),
        sa.Column("redeemed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["coupon_id"], ["coupons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_coupon_redemptions_coupon_id", "coupon_redemptions", ["coupon_id"])
    op.create_index("ix_coupon_redemptions_user_id", "coupon_redemptions", ["user_id"])
    op.create_index("ix_coupon_redemptions_redeemed_at", "coupon_redemptions", ["redeemed_at"])
    # The per-user limit check queries on exactly this pair, on every keystroke
    # in the checkout form.
    op.create_index("ix_coupon_redemptions_coupon_user", "coupon_redemptions", ["coupon_id", "user_id"])


def downgrade() -> None:
    op.drop_index("ix_coupon_redemptions_coupon_user", table_name="coupon_redemptions")
    op.drop_index("ix_coupon_redemptions_redeemed_at", table_name="coupon_redemptions")
    op.drop_index("ix_coupon_redemptions_user_id", table_name="coupon_redemptions")
    op.drop_index("ix_coupon_redemptions_coupon_id", table_name="coupon_redemptions")
    op.drop_table("coupon_redemptions")
    op.drop_index("ix_coupons_code", table_name="coupons")
    op.drop_table("coupons")
    postgresql.ENUM(name="discounttype").drop(op.get_bind(), checkfirst=True)

"""Generated-image history and real token metering.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6

Two changes that ship together because they are the same change viewed twice:
the app was recording neither what it produced nor what it cost.

**`generated_images`** — new. Image generation returned a base64 data URL and
persisted nothing; the one attempt to save it passed a keyword that is not a
column, raised `TypeError` into a bare `except`, and logged. The gallery the
user saw was six static files shipped in `public/images`.

**`usage_records`** — extended. `tokens_used` existed from the first migration
and was written as 0 on every row, because the middleware called
`record_usage()` without a count and nothing else wrote it. Every seeded plan
carries a `chat_tokens_per_day` value that therefore gated nothing. This adds
the prompt/completion split, the model attribution, and — importantly — the two
composite indexes the limit checks need. Those checks run *before* each request
is served, and without an index matching their shape they degrade into a scan
of everything the user has ever done.

Reversible: `downgrade()` drops the table and the added columns. The image
*files* on disk are not touched, deliberately — a schema rollback should not
destroy user content that a re-upgrade could still reference.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    # ── Generated image history ───────────────────────────────────────
    op.create_table(
        "generated_images",
        sa.Column("id", UUID, primary_key=True),
        # CASCADE: an erased account takes its pictures with it. The prompt is
        # user content, and a row surviving deletion would retain it after the
        # user exercised their right to erasure.
        sa.Column(
            "user_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # SET NULL, not CASCADE: deleting the conversation an image was made in
        # must not delete the image. The gallery is curated separately.
        sa.Column(
            "session_id",
            UUID,
            sa.ForeignKey("chat_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Text, not String(n): the column is Fernet-encrypted at the ORM layer,
        # and ciphertext is longer than the plaintext it holds — a length bound
        # sized for the prompt would reject prompts that fit.
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("negative_prompt", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("width", sa.Integer(), nullable=False, server_default="1024"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="1024"),
        sa.Column("seed", sa.String(64), nullable=True),
        # Relative to IMAGE_STORAGE_DIR, never absolute — the root differs
        # between the host and the container.
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=False, server_default="image/png"),
        sa.Column("byte_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_generated_images_user_id", "generated_images", ["user_id"])
    op.create_index("ix_generated_images_session_id", "generated_images", ["session_id"])
    op.create_index("ix_generated_images_is_deleted", "generated_images", ["is_deleted"])
    op.create_index("ix_generated_images_created_at", "generated_images", ["created_at"])
    # The gallery query, exactly: one user's live images, newest first.
    op.create_index(
        "ix_generated_images_user_created",
        "generated_images",
        ["user_id", "is_deleted", "created_at"],
    )

    # ── Token metering ────────────────────────────────────────────────
    # server_default on every added column so the ALTER does not fail against
    # existing rows, and so historical usage reads as "0 tokens recorded"
    # rather than NULL — which is the truth: nothing was ever recorded.
    op.add_column(
        "usage_records",
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "usage_records",
        sa.Column(
            "completion_tokens", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column("usage_records", sa.Column("model", sa.String(128), nullable=True))

    # The two hot paths. Both run before a request is served.
    op.create_index(
        "ix_usage_records_user_feature_date",
        "usage_records",
        ["user_id", "feature", "date"],
    )
    op.create_index(
        "ix_usage_records_user_feature_month",
        "usage_records",
        ["user_id", "feature", "month"],
    )


def downgrade() -> None:
    op.drop_index("ix_usage_records_user_feature_month", table_name="usage_records")
    op.drop_index("ix_usage_records_user_feature_date", table_name="usage_records")
    op.drop_column("usage_records", "model")
    op.drop_column("usage_records", "completion_tokens")
    op.drop_column("usage_records", "prompt_tokens")

    op.drop_index("ix_generated_images_user_created", table_name="generated_images")
    op.drop_index("ix_generated_images_created_at", table_name="generated_images")
    op.drop_index("ix_generated_images_is_deleted", table_name="generated_images")
    op.drop_index("ix_generated_images_session_id", table_name="generated_images")
    op.drop_index("ix_generated_images_user_id", table_name="generated_images")
    op.drop_table("generated_images")

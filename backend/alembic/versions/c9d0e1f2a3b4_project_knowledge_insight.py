"""Project knowledge: retrieval usage and extracted-text preview.

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3

All three columns are additive with defaults, so this applies to a live table
without rewriting rows. Existing files start at zero retrievals and no preview,
which is honest — we have no record of what they were used for before now, and
inventing one would make the "never used" signal untrustworthy from day one.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "project_files",
        sa.Column("retrieval_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("project_files", sa.Column("last_retrieved_at", sa.DateTime(), nullable=True))
    op.add_column("project_files", sa.Column("preview", sa.String(length=600), nullable=True))


def downgrade() -> None:
    op.drop_column("project_files", "preview")
    op.drop_column("project_files", "last_retrieved_at")
    op.drop_column("project_files", "retrieval_count")

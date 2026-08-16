"""Retain a project file's extracted text so it can be re-indexed.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4

The *text*, not the original bytes. Re-indexing re-chunks and re-embeds — it
never needs the PDF again — so storing 10MB binaries per file to support an
operation that only reads the extraction would cost a hundredfold for nothing.

Nullable, so existing rows are untouched. Files added before this cannot be
re-indexed and the API says so explicitly rather than failing obscurely.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("project_files", sa.Column("extracted_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("project_files", "extracted_text")

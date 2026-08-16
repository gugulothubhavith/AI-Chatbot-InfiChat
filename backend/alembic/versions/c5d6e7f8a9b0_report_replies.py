"""Admin replies on user reports.

`admin_notes` already existed but is deliberately internal — `ReportOut` omits
it, so it is never returned to the reporter. That left no way to answer someone
at all: a user could file a report and never hear anything back.

`admin_reply` is the user-visible answer, kept as a separate column precisely so
internal triage and the reply can never be confused for one another.

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, None] = "b4c5d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_reports", sa.Column("admin_reply", sa.String(), nullable=True))
    op.add_column("user_reports", sa.Column("replied_at", sa.DateTime(), nullable=True))
    op.add_column("user_reports", sa.Column("replied_by_email", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_reports", "replied_by_email")
    op.drop_column("user_reports", "replied_at")
    op.drop_column("user_reports", "admin_reply")

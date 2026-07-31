"""add consent fields

Revision ID: a1b2c3d4e5f6
Revises: 5aa1539be597
Create Date: 2026-07-31 00:00:00.000000

Phase 3.2: Server-side consent enforcement — migration.

Adds five consent-tracking columns to `users` (current state) and a new
`consent_events` table (append-only audit trail). NULL in the user columns
means "never consented" — existing users all start NULL after this migration,
which is why the gate in app/core/deps.py treats NULL as stale.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import app.models.types

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5aa1539be597'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add consent tracking columns to users table
    op.add_column('users', sa.Column('terms_accepted_version', sa.String(), nullable=True))
    op.add_column('users', sa.Column('privacy_accepted_version', sa.String(), nullable=True))
    op.add_column('users', sa.Column('consent_accepted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('consent_ip', sa.String(), nullable=True))
    op.add_column('users', sa.Column('consent_user_agent', sa.String(), nullable=True))

    # Create consent_events audit table (append-only)
    # user_id uses the portable UUID type to match the users table
    op.create_table('consent_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', app.models.types.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),  # 'accept', 'withdraw', 're-consent'
        sa.Column('terms_version', sa.String(), nullable=True),
        sa.Column('privacy_version', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_consent_events_user_id'), 'consent_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_consent_events_timestamp'), 'consent_events', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_consent_events_timestamp'), table_name='consent_events')
    op.drop_index(op.f('ix_consent_events_user_id'), table_name='consent_events')
    op.drop_table('consent_events')

    op.drop_column('users', 'consent_user_agent')
    op.drop_column('users', 'consent_ip')
    op.drop_column('users', 'consent_accepted_at')
    op.drop_column('users', 'privacy_accepted_version')
    op.drop_column('users', 'terms_accepted_version')

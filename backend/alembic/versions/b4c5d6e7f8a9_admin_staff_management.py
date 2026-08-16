"""Admin staff directory, credential lifecycle and audit attribution.

Adds the columns the admin console needs to manage employees:

* ``admin_profiles`` gains directory fields (name, title, department, employee
  id) and credential-lifecycle fields. ``must_change_password`` is what makes
  admin-issued initial passwords safe: the password is known to two people
  until the employee replaces it, and this flag forces that on first login.
* ``admin_audit_logs`` gains ``actor_email``, ``status`` and ``severity``.
  ``admin_id`` is ON DELETE SET NULL, so removing a staff member previously
  erased the only record of who did what; the snapshotted email keeps the trail
  attributable. ``status`` lets denied attempts be recorded rather than only
  logged to stdout.
* ``admin_invites`` gains ``accepted_at`` and ``revoked_at`` — there was no way
  to record either outcome, so every invite stayed PENDING forever.

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── admin_profiles ──────────────────────────────────────────────────
    op.add_column("admin_profiles", sa.Column("full_name", sa.String(), nullable=True))
    op.add_column("admin_profiles", sa.Column("job_title", sa.String(), nullable=True))
    op.add_column("admin_profiles", sa.Column("department", sa.String(), nullable=True))
    op.add_column("admin_profiles", sa.Column("employee_id", sa.String(), nullable=True))
    op.add_column("admin_profiles", sa.Column("notes", sa.String(), nullable=True))
    op.add_column(
        "admin_profiles",
        # server_default is required: existing rows need a value for the NOT
        # NULL constraint to hold. Existing admins are deliberately seeded
        # False — they chose their own password and should not be forced
        # through a rotation by a schema change.
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("admin_profiles", sa.Column("password_changed_at", sa.DateTime(), nullable=True))
    op.add_column("admin_profiles", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    op.add_column("admin_profiles", sa.Column("last_login_ip", sa.String(), nullable=True))
    op.create_index("ix_admin_profiles_employee_id", "admin_profiles", ["employee_id"])

    # ── admin_audit_logs ────────────────────────────────────────────────
    op.add_column("admin_audit_logs", sa.Column("actor_email", sa.String(), nullable=True))
    op.add_column(
        "admin_audit_logs",
        sa.Column("status", sa.String(), nullable=False, server_default="success"),
    )
    op.add_column(
        "admin_audit_logs",
        sa.Column("severity", sa.String(), nullable=False, server_default="info"),
    )
    op.create_index("ix_admin_audit_logs_actor_email", "admin_audit_logs", ["actor_email"])
    op.create_index("ix_admin_audit_logs_status", "admin_audit_logs", ["status"])
    op.create_index("ix_admin_audit_logs_severity", "admin_audit_logs", ["severity"])
    # The audit viewer's default query is "recent activity by this actor", and
    # the table only grows. Without this the filtered view degrades into a
    # sequential scan once the log reaches any real size.
    op.create_index(
        "ix_admin_audit_logs_timestamp_action",
        "admin_audit_logs",
        ["timestamp", "action"],
    )

    # ── admin_invites ───────────────────────────────────────────────────
    op.add_column("admin_invites", sa.Column("accepted_at", sa.DateTime(), nullable=True))
    op.add_column("admin_invites", sa.Column("revoked_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("admin_invites", "revoked_at")
    op.drop_column("admin_invites", "accepted_at")

    op.drop_index("ix_admin_audit_logs_timestamp_action", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_severity", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_status", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_actor_email", table_name="admin_audit_logs")
    op.drop_column("admin_audit_logs", "severity")
    op.drop_column("admin_audit_logs", "status")
    op.drop_column("admin_audit_logs", "actor_email")

    op.drop_index("ix_admin_profiles_employee_id", table_name="admin_profiles")
    op.drop_column("admin_profiles", "last_login_ip")
    op.drop_column("admin_profiles", "last_login_at")
    op.drop_column("admin_profiles", "password_changed_at")
    op.drop_column("admin_profiles", "must_change_password")
    op.drop_column("admin_profiles", "notes")
    op.drop_column("admin_profiles", "employee_id")
    op.drop_column("admin_profiles", "department")
    op.drop_column("admin_profiles", "job_title")
    op.drop_column("admin_profiles", "full_name")

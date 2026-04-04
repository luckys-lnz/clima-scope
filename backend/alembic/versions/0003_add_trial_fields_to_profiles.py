"""add trial fields to profiles table."""

from alembic import op
import sqlalchemy as sa

revision = "0003_add_trial_fields_to_profiles"
down_revision = "0002_create_user_settings_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "trial_status",
            sa.String(length=32),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "profiles",
        sa.Column("trial_converted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_profiles_trial_status_trial_ends_at",
        "profiles",
        ["trial_status", "trial_ends_at"],
    )

    # Rollout policy: existing users get a fresh 30-day trial window.
    op.execute(
        """
        UPDATE profiles
        SET
          trial_started_at = COALESCE(trial_started_at, timezone('utc', now())),
          trial_ends_at = COALESCE(trial_ends_at, timezone('utc', now()) + interval '30 days')
        """
    )

    # Users with an active paid subscription are marked converted immediately.
    op.execute(
        """
        UPDATE profiles p
        SET
          trial_status = 'converted',
          trial_converted_at = COALESCE(p.trial_converted_at, timezone('utc', now()))
        FROM user_subscriptions s
        WHERE s.user_id::text = p.id::text
          AND s.status = 'active'
        """
    )


def downgrade() -> None:
    op.drop_index("ix_profiles_trial_status_trial_ends_at", table_name="profiles")
    op.drop_column("profiles", "trial_converted_at")
    op.drop_column("profiles", "trial_status")
    op.drop_column("profiles", "trial_ends_at")
    op.drop_column("profiles", "trial_started_at")

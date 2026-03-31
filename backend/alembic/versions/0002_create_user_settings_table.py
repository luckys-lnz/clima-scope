"""create user_settings table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0002_create_user_settings_table"
down_revision = "0001_create_historical_weather_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("pdf_template_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("show_constituencies", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("show_wards", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("label_font_size", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("show_constituency_labels", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("show_ward_labels", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("constituency_label_font_size", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("ward_label_font_size", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("label_option", sa.String(length=32), nullable=False, server_default="none"),
        sa.Column(
            "constituency_border_color",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'#1e293b'"),
        ),
        sa.Column(
            "constituency_border_width",
            sa.REAL(),
            nullable=False,
            server_default=sa.text("1.2"),
        ),
        sa.Column(
            "constituency_border_style",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'solid'"),
        ),
        sa.Column(
            "ward_border_color",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'#2563eb'"),
        ),
        sa.Column(
            "ward_border_width",
            sa.REAL(),
            nullable=False,
            server_default=sa.text("0.9"),
        ),
        sa.Column(
            "ward_border_style",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'dashed'"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pdf_template_id"], ["pdf_templates.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id", name="unique_user_settings"),
    )


def downgrade() -> None:
    op.drop_table("user_settings")

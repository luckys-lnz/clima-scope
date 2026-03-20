"""create historical_weather_data table."""

from alembic import op
import sqlalchemy as sa

revision = "0001_create_historical_weather_data"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the table that stores monthly snapshots of Open-Meteo data."""
    op.create_table(
        "historical_weather_data",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("county_id", sa.String(length=6), nullable=False),
        sa.Column("county_name", sa.String(length=128), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("variable", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("units", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="open_meteo"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "county_id",
            "date",
            "variable",
            "source",
            name="uq_historical_weather_data_county_date_variable_source",
        ),
    )

    op.create_index(
        "ix_historical_weather_data_county_date",
        "historical_weather_data",
        ["county_id", "date"],
    )


def downgrade() -> None:
    """Drop the historical data table."""
    op.drop_index("ix_historical_weather_data_county_date", table_name="historical_weather_data")
    op.drop_table("historical_weather_data")

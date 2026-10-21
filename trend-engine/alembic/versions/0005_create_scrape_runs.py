"""create scrape_runs and dropped_records

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-30
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scrape_runs",
        sa.Column("run_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.brand_id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),  # success | partial | failed
        sa.Column("products_seen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("products_kept", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("run_date", "brand_id"),
    )
    op.create_index("ix_scrape_runs_run_date", "scrape_runs", ["run_date"])

    op.create_table(
        "dropped_records",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.brand_id"), nullable=True),
        sa.Column("reason", sa.String(), nullable=False),  # non_clothing_accessory, ...
        sa.Column("raw_title", sa.String(), nullable=True),
        sa.Column("raw_payload", JSONB(), nullable=True),
    )
    op.create_index("ix_dropped_records_run_date_reason", "dropped_records", ["run_date", "reason"])

    # backfill: assume success for every (date, brand) already in observations
    op.execute(
        """
        INSERT INTO scrape_runs (run_date, brand_id, status, products_seen, products_kept)
        SELECT DISTINCT o.obs_date, p.brand_id, 'success', 0, 0
        FROM observations o
        JOIN products p ON p.product_id = o.product_id
        ON CONFLICT (run_date, brand_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("dropped_records")
    op.drop_table("scrape_runs")

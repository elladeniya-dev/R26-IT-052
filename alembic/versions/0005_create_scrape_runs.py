"""create scrape_runs and dropped_records

THE CRITICAL TABLE (architecture spec §1/§5). Without scrape_runs, a brand
that failed to scrape on a given day is indistinguishable from every one of
its products having genuinely disappeared — the trend engine's restock/
disappearance signal depends on this table to mask brand-day validity (see
app/ml/features.py build_panel()).

Includes a backfill: status='success' for every (run_date, brand_id) pair
already present in observations, since real per-brand failure history wasn't
recorded before this table existed. On a fresh database this is a no-op
(observations is empty at this point in the migration chain) — it only does
real work if ever run against a database where observations was already
populated by some other means. Flagged here, not hidden, per spec §6: this
backfill is an assumption, not a real record of what actually failed.

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

    # ASSUMPTION BACKFILL — see module docstring.
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

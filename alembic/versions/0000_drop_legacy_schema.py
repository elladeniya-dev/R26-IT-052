"""drop legacy schema

Removes the previous architecture's tables (products, trend_observations,
trend_signals, attribute_mappings, product_trend_metrics) to make room for
the new normalized schema — 'products' collides by name with the new
products table. Confirmed with the user before running (real live data:
3,592 products / 10,112 observations / 228 trend signals / 307 attribute
mappings at drop time).

Nothing is actually lost: the real original data is the raw scrape JSON in
trend-data-collector/output/run_*/, which jobs/ingest.py reprocesses into the
new schema. What's dropped here is already-computed derived data (old
taxonomy mappings, old trend signals) the new pipeline recomputes differently
anyway (no canonicalization — see architecture spec §2).

Revision ID: 0000
Revises:
Create Date: 2026-08-30
"""
from alembic import op

revision = "0000"
down_revision = None
branch_labels = None
depends_on = None

LEGACY_TABLES = [
    "product_trend_metrics",  # FK -> products
    "trend_observations",
    "trend_signals",
    "attribute_mappings",
    "products",
]


def upgrade() -> None:
    for table in LEGACY_TABLES:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')


def downgrade() -> None:
    raise NotImplementedError(
        "Legacy table data was not backed up before dropping — this cannot be undone. "
        "Restore from a database snapshot/backup if one exists."
    )

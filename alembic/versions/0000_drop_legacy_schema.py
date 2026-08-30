"""drop legacy schema

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

"""create product_lifecycle view

Derived aggregates (first/last seen, days observed, price range, best rank,
still-listed) are never stored as columns — every scrape would have to
rewrite them, and any bug would leave the table silently inconsistent with
observations (architecture spec §1/§2.1). This view recomputes them on every
read instead, so they can never drift out of sync.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-30
"""
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

VIEW_SQL = """
CREATE VIEW product_lifecycle AS
SELECT p.product_id,
       p.brand_id,
       p.first_seen,
       MAX(o.obs_date)                        AS last_seen,
       COUNT(*)                               AS days_observed,
       MIN(o.price_lkr)                       AS price_min_lkr,
       MAX(o.price_lkr)                       AS price_max_lkr,
       (ARRAY_AGG(o.price_lkr ORDER BY o.obs_date DESC))[1] AS price_last_lkr,
       MIN(o.rank_position)                   AS rank_best,
       MAX(o.obs_date) = (SELECT MAX(obs_date) FROM observations) AS is_still_listed
FROM products p
JOIN observations o USING (product_id)
GROUP BY p.product_id, p.brand_id, p.first_seen
"""


def upgrade() -> None:
    op.execute(VIEW_SQL)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS product_lifecycle")

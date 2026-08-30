"""create observations

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-30
"""
import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "observations",
        sa.Column("obs_date", sa.Date(), primary_key=True),
        sa.Column(
            "product_id", sa.String(),
            sa.ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column("price_lkr", sa.Numeric(12, 2), nullable=True),
        sa.Column("compare_at_lkr", sa.Numeric(12, 2), nullable=True),  # original price when on sale
        sa.Column("rank_position", sa.Integer(), nullable=True),
        sa.Column("is_on_sale", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_new_arrival", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("in_stock", sa.Boolean(), nullable=True),
    )
    op.create_index("ix_observations_product_date", "observations", ["product_id", "obs_date"])
    op.create_index("ix_observations_obs_date", "observations", ["obs_date"])


def downgrade() -> None:
    op.drop_table("observations")

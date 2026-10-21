"""create trend_segments (scores for attribute combinations such as "white + dress")

A separate table, not new values on the shared attr_type enum: segment types are not product attributes,
and extending that enum would let product_attributes accept them.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-19
"""
import sqlalchemy as sa

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trend_segments",
        sa.Column(
            "snapshot_id", sa.BigInteger(),
            sa.ForeignKey("trend_snapshots.snapshot_id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column("segment_type", sa.String(), primary_key=True),   # e.g. color_x_category
        sa.Column("segment_value", sa.String(), primary_key=True),  # e.g. white + dress
        sa.Column("part1_type", sa.String(), nullable=False),
        sa.Column("part1_value", sa.String(), nullable=False),
        sa.Column("part2_type", sa.String(), nullable=False),
        sa.Column("part2_value", sa.String(), nullable=False),
        sa.Column("rank_in_type", sa.SmallInteger(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("share_pct", sa.Float(), nullable=True),
        sa.Column("share_change_pct", sa.Float(), nullable=True),
        sa.Column("restock_rate", sa.Float(), nullable=True),
        sa.Column("disappear_rate", sa.Float(), nullable=True),
        sa.Column("breadth", sa.Float(), nullable=True),
        sa.Column("stores_carrying", sa.SmallInteger(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=True),
        sa.Column("lifecycle_stage", sa.String(), nullable=True),
        sa.Column("mk_p", sa.Float(), nullable=True),
    )
    op.create_index("ix_trend_segments_snapshot_score", "trend_segments", ["snapshot_id", "score"])


def downgrade() -> None:
    op.drop_table("trend_segments")

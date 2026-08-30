"""create trend_snapshots and trend_scores

Empty — the first snapshot is written by jobs/compute_trends.py, never by
this migration. Scoring never runs inside a migration or a request
(architecture spec §4.1/§5).

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-30
"""
import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trend_snapshots",
        sa.Column("snapshot_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("horizon_days", sa.SmallInteger(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False),  # 'trendnet+mrtf'
        sa.Column("model_ic", sa.Float(), nullable=True),  # validated IC, for provenance
        sa.Column("window_days", sa.SmallInteger(), nullable=False),
        sa.UniqueConstraint("as_of_date", "horizon_days", "model_name"),
    )

    op.create_table(
        "trend_scores",
        sa.Column(
            "snapshot_id", sa.BigInteger(),
            sa.ForeignKey("trend_snapshots.snapshot_id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column("attr_type", sa.Enum(name="attr_type", create_type=False), primary_key=True),
        sa.Column("attr_value", sa.String(), primary_key=True),
        sa.Column("rank_in_type", sa.SmallInteger(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("share_pct", sa.Float(), nullable=True),
        sa.Column("share_change_pct", sa.Float(), nullable=True),
        sa.Column("restock_rate", sa.Float(), nullable=True),
        sa.Column("disappear_rate", sa.Float(), nullable=True),
        sa.Column("breadth", sa.Float(), nullable=True),
        sa.Column("stores_carrying", sa.SmallInteger(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=True),  # high | medium | low
        sa.Column("lifecycle_stage", sa.String(), nullable=True),  # emerging | peaking | declining | stable
        sa.Column("mk_p", sa.Float(), nullable=True),
    )
    op.create_index("ix_trend_scores_snapshot_type_rank", "trend_scores", ["snapshot_id", "attr_type", "rank_in_type"])


def downgrade() -> None:
    op.drop_table("trend_scores")
    op.drop_table("trend_snapshots")

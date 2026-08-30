from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.product import AttrType


class TrendSnapshot(Base):
    """Precomputed once per day by jobs/compute_trends.py. The API only ever
    reads trend_scores for the latest snapshot — scoring never runs inside a
    request (architecture spec §4.1/§5)."""

    __tablename__ = "trend_snapshots"
    __table_args__ = (UniqueConstraint("as_of_date", "horizon_days", "model_name"),)

    snapshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    horizon_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)  # 'trendnet+mrtf'
    model_ic: Mapped[float | None] = mapped_column(Float)  # validated IC, for provenance
    window_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class TrendScore(Base):
    __tablename__ = "trend_scores"

    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("trend_snapshots.snapshot_id", ondelete="CASCADE"), primary_key=True
    )
    attr_type: Mapped[AttrType] = mapped_column(Enum(AttrType, name="attr_type"), primary_key=True)
    attr_value: Mapped[str] = mapped_column(String, primary_key=True)
    rank_in_type: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    share_pct: Mapped[float | None] = mapped_column(Float)
    share_change_pct: Mapped[float | None] = mapped_column(Float)
    restock_rate: Mapped[float | None] = mapped_column(Float)
    disappear_rate: Mapped[float | None] = mapped_column(Float)
    breadth: Mapped[float | None] = mapped_column(Float)
    stores_carrying: Mapped[int | None] = mapped_column(SmallInteger)
    confidence: Mapped[str | None] = mapped_column(String)  # high | medium | low
    lifecycle_stage: Mapped[str | None] = mapped_column(String)  # emerging | peaking | declining | stable
    mk_p: Mapped[float | None] = mapped_column(Float)

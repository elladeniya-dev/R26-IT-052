from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScrapeRun(Base):
    """THE CRITICAL TABLE — see architecture spec §1/§5. Without this, a
    brand's failed scrape is indistinguishable from every one of its products
    genuinely disappearing, which corrupts the restock/disappearance signal
    the trend engine's MRTF half depends on (see trend_engine.py _build():
    dis_mask is masked by brand-day validity from this table)."""

    __tablename__ = "scrape_runs"
    __table_args__ = (UniqueConstraint("run_date", "brand_id"),)

    run_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.brand_id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # success | partial | failed
    products_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    products_kept: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(String)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DroppedRecord(Base):
    __tablename__ = "dropped_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brands.brand_id"))
    reason: Mapped[str] = mapped_column(String, nullable=False)  # non_clothing_accessory, ...
    raw_title: Mapped[str | None] = mapped_column(String)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)

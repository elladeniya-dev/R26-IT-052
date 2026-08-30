import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AttrType(str, enum.Enum):
    category = "category"
    color = "color"
    pattern = "pattern"
    fabric = "fabric"
    sleeve_length = "sleeve_length"
    garment_length = "garment_length"
    neckline = "neckline"
    style_detail = "style_detail"


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String, primary_key=True)  # brand_slug:native_id
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.brand_id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)  # normalised, H&M taxonomy
    raw_product_type: Mapped[str | None] = mapped_column(String)  # what the site actually said
    product_url: Mapped[str | None] = mapped_column(String)
    image_url: Mapped[str | None] = mapped_column(String)
    published_date: Mapped[date | None] = mapped_column(Date)
    num_images: Mapped[int | None] = mapped_column(SmallInteger)
    has_rich_desc: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_tier: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    first_seen: Mapped[date] = mapped_column(Date, nullable=False)  # set once, never updated
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProductAttribute(Base):
    """One row per (product, attr_type, value). Never canonicalised — see the
    accuracy ablation in the architecture spec (§2): merging synonyms like
    navy/dark blue or spandex/lycra/elastane measurably lowered IC."""

    __tablename__ = "product_attributes"

    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True
    )
    attr_type: Mapped[AttrType] = mapped_column(Enum(AttrType, name="attr_type"), primary_key=True)
    attr_value: Mapped[str] = mapped_column(String, primary_key=True)  # lowercase, trimmed, RAW label
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ProductLifecycle(Base):
    """Read-only mapping onto the product_lifecycle VIEW (see alembic migration
    0006). Derived aggregates (first/last seen, price range, best rank,
    still-listed) are never stored — they're recomputed from observations on
    every read so they can never drift out of sync."""

    __tablename__ = "product_lifecycle"
    __table_args__ = {"info": {"is_view": True}}

    product_id: Mapped[str] = mapped_column(String, primary_key=True)
    brand_id: Mapped[int] = mapped_column()
    first_seen: Mapped[date] = mapped_column(Date)
    last_seen: Mapped[date | None] = mapped_column(Date)
    days_observed: Mapped[int] = mapped_column()
    price_min_lkr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    price_max_lkr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    price_last_lkr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    rank_best: Mapped[int | None] = mapped_column()
    is_still_listed: Mapped[bool] = mapped_column(Boolean)

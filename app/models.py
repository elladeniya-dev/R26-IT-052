from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime, timezone

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    item_id = Column(String, primary_key=True, index=True)

    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=True)

    color = Column(ARRAY(String), nullable=True)
    style = Column(ARRAY(String), nullable=True)

    brand = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String, default="LKR")

    material = Column(String, nullable=True)
    pattern = Column(String, nullable=True)
    fit_type = Column(String, nullable=True)
    target_gender = Column(String, nullable=True)

    image_url = Column(String, nullable=True)
    product_url = Column(String, nullable=True)
    source = Column(String, nullable=True)
    description = Column(String, nullable=True)

    availability = Column(Boolean, default=True)
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProductTrendMetric(Base):
    __tablename__ = "product_trend_metrics"

    metric_id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    item_id = Column(String, ForeignKey("products.item_id"), nullable=False)

    view_count = Column(Integer, default=0)
    wishlist_count = Column(Integer, default=0)
    sales_volume = Column(Integer, default=0)
    social_mentions = Column(Integer, default=0)

    availability = Column(Boolean, default=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TrendObservation(Base):
    __tablename__ = "trend_observations"

    observation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    source_name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)

    attribute_type = Column(String, nullable=False)
    attribute_value = Column(String, nullable=False)

    keyword = Column(String, nullable=True)
    mention_count = Column(Integer, default=1)
    rank_position = Column(Integer, nullable=True)

    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TrendSignal(Base):
    __tablename__ = "trend_signals"

    trend_id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    attribute_type = Column(String, nullable=False)
    attribute_value = Column(String, nullable=False)

    trend_score = Column(Float, nullable=False)
    growth_rate = Column(Float, nullable=False)

    time_window = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
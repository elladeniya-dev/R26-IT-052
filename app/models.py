from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer
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

    image_url = Column(String, nullable=True)
    product_url = Column(String, nullable=True)
    source = Column(String, nullable=True)
    description = Column(String, nullable=True)

    availability = Column(Boolean, default=True)
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
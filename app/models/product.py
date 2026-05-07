from sqlalchemy import Column, String, Float, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    item_id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=True)

    color = Column(JSONB, nullable=False)
    style = Column(JSONB, nullable=False)

    brand = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String, nullable=True)

    image_url = Column(Text, nullable=False)
    product_url = Column(Text, nullable=False)
    source = Column(String, nullable=False)

    description = Column(Text, nullable=True)
    availability = Column(Boolean, default=True)

    collected_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
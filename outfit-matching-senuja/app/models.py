from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    item_id = Column(String, primary_key=True, index=True)

    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=True)

    color = Column(JSON, nullable=False)
    style = Column(JSON, nullable=False)

    brand = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String, nullable=True)

    image_url = Column(String, nullable=True)
    product_url = Column(String, nullable=True)

    source = Column(String, nullable=True)
    description = Column(String, nullable=True)

    availability = Column(Boolean, default=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
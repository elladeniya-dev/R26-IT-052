from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
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


class OutfitSuggestion(Base):
    __tablename__ = "outfit_suggestions"

    outfit_id = Column(String, primary_key=True, index=True)
    generation_batch_id = Column(String, nullable=True, index=True)

    user_id = Column(String, nullable=False, index=True)
    selected_item_id = Column(String, nullable=False)

    compatibility_score = Column(Float, nullable=False)
    reason_tags = Column(JSON, nullable=True)

    is_saved = Column(Boolean, default=False, index=True)

    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship(
        "OutfitItem",
        back_populates="outfit",
        cascade="all, delete-orphan"
    )


class OutfitItem(Base):
    __tablename__ = "outfit_items"

    outfit_item_id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    outfit_id = Column(
        String,
        ForeignKey("outfit_suggestions.outfit_id", ondelete="CASCADE"),
        nullable=False
    )

    item_id = Column(String, nullable=False)
    role = Column(String, nullable=False)

    outfit = relationship("OutfitSuggestion", back_populates="items")
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class ProductCreate(BaseModel):
    item_id: str
    title: str
    category: str
    subcategory: Optional[str] = None
    color: Optional[List[str]] = []
    style: Optional[List[str]] = []
    brand: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "LKR"
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None
    availability: Optional[bool] = True
    collected_at: Optional[datetime] = None


class ProductResponse(ProductCreate):
    class Config:
        from_attributes = True


class TrendSignalResponse(BaseModel):
    trend_id: int
    attribute_type: str
    attribute_value: str
    trend_score: float
    growth_rate: float
    time_window: str
    start_date: datetime
    end_date: datetime
    generated_at: datetime

    class Config:
        from_attributes = True
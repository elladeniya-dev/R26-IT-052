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

    material: Optional[str] = None
    pattern: Optional[str] = None
    fit_type: Optional[str] = None
    target_gender: Optional[str] = None

    image_url: Optional[str] = None
    product_url: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None

    availability: Optional[bool] = True
    collected_at: Optional[datetime] = None


class ProductResponse(ProductCreate):
    class Config:
        from_attributes = True


class ProductTrendMetricCreate(BaseModel):
    item_id: str
    view_count: Optional[int] = 0
    wishlist_count: Optional[int] = 0
    sales_volume: Optional[int] = 0
    social_mentions: Optional[int] = 0
    availability: Optional[bool] = True
    recorded_at: Optional[datetime] = None


class ProductTrendMetricResponse(ProductTrendMetricCreate):
    metric_id: int

    class Config:
        from_attributes = True


class TrendObservationCreate(BaseModel):
    source_name: str
    source_type: str
    attribute_type: str
    attribute_value: str
    keyword: Optional[str] = None
    mention_count: Optional[int] = 1
    rank_position: Optional[int] = None
    collected_at: Optional[datetime] = None

class BulkTrendObservationCreate(BaseModel):
    observations: List[TrendObservationCreate]

class TrendObservationResponse(TrendObservationCreate):
    observation_id: int

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
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class NewArrivalItem(BaseModel):
    item_id: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    color: Optional[List[str]] = []
    material: Optional[str] = None
    fit_type: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    collected_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NewArrivalsResponse(BaseModel):
    total: int
    items: list[NewArrivalItem]


class DiscountedItem(BaseModel):
    item_id: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    price: float
    original_price: float
    discount_pct: float
    availability: bool
    image_url: Optional[str] = None
    product_url: Optional[str] = None

    class Config:
        from_attributes = True


class DiscountedItemsResponse(BaseModel):
    total: int
    items: list[DiscountedItem]


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

class TrendPredictionRequest(BaseModel):
    attribute_type: str
    attribute_value: str
    purchase_count: int
    previous_purchase_count: int
    mention_growth: int
    growth_rate: float
    weekly_rank: int
    previous_rank: int
    rank_change: int
    count_score: float
    growth_score: float
    rank_score: float
    trend_score: float

class TrendPredictionResponse(BaseModel):
    attribute_type: str
    attribute_value: str
    predicted_trend_label: str
    confidence_scores: dict
    model_type: str

class LatestTrendPredictionItem(BaseModel):
    trend_id: int
    attribute_type: str
    attribute_value: str
    trend_score: float
    growth_rate: float
    predicted_trend_label: str
    confidence_scores: dict
    model_type: str

class LatestTrendPredictionsResponse(BaseModel):
    total_predictions: int
    predictions: list[LatestTrendPredictionItem]

class TrendInsightItem(BaseModel):
    trend_id: int
    title: str
    summary: str
    reason: str
    attribute_type: str
    attribute_value: str
    trend_score: float
    growth_rate: float
    trend_status: str
    confidence: float
    display_badge: str

class TrendInsightsResponse(BaseModel):
    total_insights: int
    insights: list[TrendInsightItem]

class OutfitPredictionResponse(BaseModel):
    category: str
    colors: list[str]
    patterns: list[str]
    predicted_change: Optional[float] = None
    model_type: str

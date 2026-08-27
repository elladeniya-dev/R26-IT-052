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
    original_price: Optional[float] = None


class ProductResponse(ProductCreate):
    class Config:
        from_attributes = True


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
    model_type: str = "TFT + Lift-Filtered Grounding"

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class TrendScoreOut(BaseModel):
    attr_type: str
    attr_value: str
    rank_in_type: int
    score: float
    share_pct: float | None
    share_change_pct: float | None
    restock_rate: float | None
    disappear_rate: float | None
    breadth: float | None
    stores_carrying: int | None
    confidence: str | None
    lifecycle_stage: str | None
    mk_p: float | None


class TrendsResponse(BaseModel):
    category: list[TrendScoreOut] = []
    color: list[TrendScoreOut] = []
    pattern: list[TrendScoreOut] = []
    fabric: list[TrendScoreOut] = []
    sleeve_length: list[TrendScoreOut] = []
    garment_length: list[TrendScoreOut] = []
    neckline: list[TrendScoreOut] = []
    style_detail: list[TrendScoreOut] = []


class TrendHistoryPoint(BaseModel):
    as_of_date: date
    score: float
    share_pct: float | None
    rank_in_type: int


class TrendingProductOut(BaseModel):
    item_id: str
    title: str
    category: str
    color: list[str]
    style: list[str]
    brand: str
    source: str
    price: float
    image_url: str
    product_url: str
    trend_score: float
    trend_reason: str


class TrendMetaResponse(BaseModel):
    model_name: str
    model_ic: float | None
    as_of_date: date
    horizon_days: int
    window_days: int
    computed_at: datetime


class ProductDescriptor(BaseModel):
    """A partner product, reduced to the fields needed to describe it. Nothing is stored."""
    id: str
    title: str = ""
    description: str = ""
    category: str = ""
    subcategory: str = ""
    colors: list[str] = []
    tags: list[str] = []


class ScoreProductsRequest(BaseModel):
    products: list[ProductDescriptor] = Field(max_length=500)
    horizon: Literal[3, 5] = 3


class ProductTrendMatch(BaseModel):
    attr_type: str
    attr_value: str
    match: str
    trend_score: float
    confidence: str
    contribution: float


class SegmentPart(BaseModel):
    attr_type: str
    attr_value: str


class SegmentScoreOut(BaseModel):
    """A rising or falling attribute combination, e.g. 'white + dress'."""
    segment_type: str
    segment: str
    parts: list[SegmentPart]
    rank_in_type: int
    score: float
    share_pct: float | None
    share_change_pct: float | None
    stores_carrying: int | None
    confidence: str | None
    lifecycle_stage: str | None


class ProductSegmentMatch(BaseModel):
    segment_type: str
    segment: str
    parts: list[SegmentPart]
    match: str
    trend_score: float
    confidence: str
    contribution: float


class ProductTrendOut(BaseModel):
    id: str
    # Single-attribute view (unchanged): how many rising attributes the product carries.
    trend_score: float
    matches: list[ProductTrendMatch]
    # Cloth-level view: only products that carry BOTH parts of a rising segment score here.
    segment_score: float = 0.0
    segments: list[ProductSegmentMatch] = []

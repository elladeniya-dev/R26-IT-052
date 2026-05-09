from pydantic import BaseModel
from typing import List, Optional


class RecommendationRequest(BaseModel):
    user_id: str
    preferred_categories: List[str]
    preferred_colors: List[str]
    preferred_styles: List[str]
    preferred_brands: Optional[List[str]] = []
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    max_results: Optional[int] = 5


class RecommendedProduct(BaseModel):
    item_id: str
    title: str
    category: str
    color: List[str]
    style: List[str]
    brand: Optional[str] = None
    price: Optional[float] = None
    image_url: str
    product_url: str
    final_score: float
    user_match_score: float
    product_quality_score: float
    reason_tags: List[str]


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[RecommendedProduct]

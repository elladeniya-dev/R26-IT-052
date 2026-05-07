from pydantic import BaseModel
from typing import List, Optional


class RecommendationRequest(BaseModel):
    user_id: str
    preferred_categories: List[str]
    preferred_colors: List[str]
    preferred_styles: List[str]
    max_results: Optional[int] = 5


class RecommendedProduct(BaseModel):
    item_id: str
    title: str
    category: str
    color: List[str]
    style: List[str]
    price: Optional[float] = None
    image_url: str
    product_url: str
    final_score: float
    reason_tags: List[str]


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[RecommendedProduct]
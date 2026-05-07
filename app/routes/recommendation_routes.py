from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.recommendation_schema import (
    RecommendationRequest,
    RecommendationResponse
)
from app.services.recommendation_service import generate_recommendations

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.post("/", response_model=RecommendationResponse)
def recommend_products(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    recommendations = generate_recommendations(db, request)

    return {
        "user_id": request.user_id,
        "recommendations": recommendations
    }
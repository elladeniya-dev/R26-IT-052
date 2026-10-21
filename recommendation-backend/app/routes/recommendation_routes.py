from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.recommendation_schema import (
    ChalaRecommendationRequest,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.chala_preference_client import get_chala_enriched_preferences
from app.services.recommendation_service import generate_recommendations

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.post("/", response_model=RecommendationResponse)
def recommend_products(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
):
    """
    Existing manual recommendation endpoint.

    This endpoint accepts preferences directly from the request body.
    It is useful for testing the recommendation engine manually.
    """

    recommendations = generate_recommendations(db, request)

    return {
        "user_id": request.user_id,
        "applied_preferences": None,
        "recommendations": recommendations,
    }


@router.post("/from-chala", response_model=RecommendationResponse)
def recommend_products_from_chala(
    request: ChalaRecommendationRequest,
    db: Session = Depends(get_db),
):
    """
    Integrated recommendation endpoint.

    This endpoint receives only user_id, gets the enriched preference
    profile from Chala's backend, and generates Koji product recommendations.
    """

    chala_preferences = get_chala_enriched_preferences(request.user_id)

    recommendation_request = RecommendationRequest(
        user_id=request.user_id,
        preferred_categories=chala_preferences["categories"],
        preferred_colors=chala_preferences["colors"],
        preferred_styles=chala_preferences["styles"],
        preferred_brands=chala_preferences["preferred_brands"],
        category_weights=chala_preferences["category_weights"],
        color_weights=chala_preferences["color_weights"],
        style_weights=chala_preferences["style_weights"],
        brand_weights=chala_preferences["brand_weights"],
        occasion_weights=chala_preferences["occasion_weights"],
        preference_sources=chala_preferences["preference_sources"],
        price_min=request.price_min,
        price_max=request.price_max,
        style_filter=request.style_filter,
        max_results=request.max_results,
    )

    recommendations = generate_recommendations(db, recommendation_request)

    return {
        "user_id": request.user_id,
        "applied_preferences": {
            "categories": chala_preferences["categories"],
            "colors": chala_preferences["colors"],
            "styles": chala_preferences["styles"],
            "occasions": chala_preferences["occasions"],
            "preferred_brands": chala_preferences["preferred_brands"],
        },
        "recommendations": recommendations,
    }

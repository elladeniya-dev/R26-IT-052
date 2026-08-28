from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.core.database import get_db
from app.core.koji_database import get_koji_db
from app.services.recommendation_service import get_recommendations

router = APIRouter(tags=["Recommendations"])


@router.post("/recommendations/", response_model=schemas.RecommendationsResponse)
def post_recommendations(
    request: schemas.RecommendationRequest,
    db: Session = Depends(get_db),
    koji_db: Session = Depends(get_koji_db),
):
    """
    Ranks live products from the Koji catalog against the user's stated
    preferences, weighted by real current trend signals from our own
    TrendSignal data. See app/services/recommendation_service.py for the
    scoring formula.
    """
    results = get_recommendations(
        db=db,
        koji_db=koji_db,
        preferred_categories=request.preferred_categories,
        preferred_colors=request.preferred_colors,
        preferred_styles=request.preferred_styles,
        preferred_brands=request.preferred_brands,
        price_min=request.price_min,
        price_max=request.price_max,
        max_results=request.max_results,
    )
    return {"recommendations": results}

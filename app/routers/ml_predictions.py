from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.core.database import get_db
from app.services.ml_prediction_service import trend_ml_service

router = APIRouter(prefix="/ml", tags=["Machine Learning Predictions"])

@router.get("/predict-outfits", response_model=List[schemas.OutfitPredictionResponse])
def get_trending_outfits(top_k: int = 1, db: Session = Depends(get_db)):
    """
    Predicts trending outfits: category comes from a joint-attribute LightGBM
    forecast (app/pipeline/joint_trend_forecast.py) run against our real Sri Lankan
    scrape history; colors/patterns are grounded via lift-filtered
    co-occurrence against live inventory. Returns [] if no attribute
    combination yet has enough history (>= 6 weeks) to forecast — never a
    hardcoded fallback category.
    """
    predictions = trend_ml_service.predict_trending_outfit(top_k_categories=top_k)
    return predictions

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
    Predicts trending outfits using a Temporal Fusion Transformer (TFT) 
    for category forecasting, grounded by a Pandas Lift-Filtered MBA lookup 
    to prevent style hallucinations.
    """
    
    # Normally we would fetch transactions from the DB here:
    # transactions = db.query(models.Product).all()
    # df = pd.DataFrame([t.__dict__ for t in transactions])
    # For now, we rely on the ML service to mock the H&M DataFrame.
    
    predictions = trend_ml_service.predict_trending_outfit(top_k_categories=top_k)
    return predictions

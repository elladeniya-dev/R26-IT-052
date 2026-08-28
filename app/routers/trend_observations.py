from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db

router = APIRouter(tags=["Trend Observations"])


@router.get("/trend-observations/")
def get_all_trend_observations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    observations = db.query(models.TrendObservation).offset(skip).limit(limit).all()
    total_observations = db.query(models.TrendObservation).count()

    return {
        "total_observations": total_observations,
        "returned_count": len(observations),
        "observations": observations,
    }

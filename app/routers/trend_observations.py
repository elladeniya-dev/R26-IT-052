from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db

router = APIRouter(tags=["Trend Observations"])


@router.post("/trend-observations/bulk")
def create_bulk_trend_observations(
    bulk_data: schemas.BulkTrendObservationCreate,
    db: Session = Depends(get_db),
):
    if not bulk_data.observations:
        raise HTTPException(
            status_code=400,
            detail="Observation list cannot be empty",
        )

    new_observations = []

    for observation in bulk_data.observations:
        new_observation = models.TrendObservation(
            source_name=observation.source_name,
            source_type=observation.source_type,
            attribute_type=observation.attribute_type,
            attribute_value=observation.attribute_value,
            keyword=observation.keyword,
            mention_count=observation.mention_count,
            rank_position=observation.rank_position,
            collected_at=observation.collected_at,
        )

        db.add(new_observation)
        new_observations.append(new_observation)

    db.commit()

    for observation in new_observations:
        db.refresh(observation)

    return {
        "message": "Bulk trend observations inserted successfully",
        "inserted_count": len(new_observations),
        "observations": new_observations,
    }


@router.post("/trend-observations/", response_model=schemas.TrendObservationResponse)
def create_trend_observation(
    observation: schemas.TrendObservationCreate,
    db: Session = Depends(get_db),
):
    new_observation = models.TrendObservation(
        source_name=observation.source_name,
        source_type=observation.source_type,
        attribute_type=observation.attribute_type,
        attribute_value=observation.attribute_value,
        keyword=observation.keyword,
        mention_count=observation.mention_count,
        rank_position=observation.rank_position,
        collected_at=observation.collected_at,
    )

    db.add(new_observation)
    db.commit()
    db.refresh(new_observation)

    return new_observation


@router.get("/trend-observations/")
def get_all_trend_observations(db: Session = Depends(get_db)):
    observations = db.query(models.TrendObservation).all()

    return {
        "total_observations": len(observations),
        "observations": observations,
    }

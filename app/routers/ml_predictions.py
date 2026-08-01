from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.core.constants import is_safe_user_facing_trend
from app.services.ml_prediction_service import trend_ml_service
from app.services.trend_analysis_service import derive_prediction_features_from_signal

router = APIRouter(prefix="/ml", tags=["Machine Learning Predictions"])


@router.post("/predict-trend", response_model=schemas.TrendPredictionResponse)
def predict_trend_with_ml(request: schemas.TrendPredictionRequest):
    prediction = trend_ml_service.predict_trend_label(
        attribute_type=request.attribute_type,
        attribute_value=request.attribute_value,
        purchase_count=request.purchase_count,
        previous_purchase_count=request.previous_purchase_count,
        mention_growth=request.mention_growth,
        growth_rate=request.growth_rate,
        weekly_rank=request.weekly_rank,
        previous_rank=request.previous_rank,
        rank_change=request.rank_change,
        count_score=request.count_score,
        growth_score=request.growth_score,
        rank_score=request.rank_score,
        trend_score=request.trend_score,
    )
    return prediction


@router.get(
    "/latest-trend-predictions",
    response_model=schemas.LatestTrendPredictionsResponse,
)
def get_latest_trend_predictions(db: Session = Depends(get_db)):
    latest_trend = (
        db.query(models.TrendSignal)
        .order_by(models.TrendSignal.end_date.desc())
        .first()
    )

    if not latest_trend:
        return {
            "total_predictions": 0,
            "predictions": [],
        }

    latest_signals = (
        db.query(models.TrendSignal)
        .filter(
            models.TrendSignal.time_window == latest_trend.time_window,
            models.TrendSignal.start_date == latest_trend.start_date,
            models.TrendSignal.end_date == latest_trend.end_date,
        )
        .order_by(models.TrendSignal.trend_score.desc())
        .all()
    )

    predictions = []

    for index, signal in enumerate(latest_signals, start=1):
        if not is_safe_user_facing_trend(
            signal.attribute_type,
            signal.attribute_value,
        ):
            continue

        features = derive_prediction_features_from_signal(signal, index)

        prediction = trend_ml_service.predict_trend_label(**features)

        predictions.append(
            {
                "trend_id": signal.trend_id,
                "attribute_type": signal.attribute_type,
                "attribute_value": signal.attribute_value,
                "trend_score": features["trend_score"],
                "growth_rate": features["growth_rate"],
                "predicted_trend_label": prediction["predicted_trend_label"],
                "confidence_scores": prediction["confidence_scores"],
                "model_type": prediction["model_type"],
            }
        )

    return {
        "total_predictions": len(predictions),
        "predictions": predictions,
    }

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.core.constants import is_safe_user_facing_trend
from app.services.ml_prediction_service import trend_ml_service
from app.services.trend_analysis_service import derive_prediction_features_from_signal
from app.services.trend_insight_service import (
    build_trend_title,
    build_trend_summary,
    build_trend_reason,
    get_display_badge,
)

router = APIRouter(tags=["Trend Insights"])


@router.get("/trend-insights", response_model=schemas.TrendInsightsResponse)
def get_trend_insights(db: Session = Depends(get_db)):
    latest_trend = (
        db.query(models.TrendSignal)
        .order_by(models.TrendSignal.end_date.desc())
        .first()
    )

    if not latest_trend:
        return {
            "total_insights": 0,
            "insights": [],
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

    insights = []

    for index, signal in enumerate(latest_signals, start=1):
        if not is_safe_user_facing_trend(
            signal.attribute_type,
            signal.attribute_value,
        ):
            continue

        if len(insights) >= 20:
            break

        features = derive_prediction_features_from_signal(signal, index)
        prediction = trend_ml_service.predict_trend_label(**features)

        trend_status = prediction["predicted_trend_label"]
        confidence_scores = prediction["confidence_scores"]
        confidence = float(confidence_scores.get(trend_status, 0))

        insights.append(
            {
                "trend_id": signal.trend_id,
                "title": build_trend_title(
                    signal.attribute_type,
                    signal.attribute_value,
                    trend_status,
                ),
                "summary": build_trend_summary(
                    signal.attribute_type,
                    signal.attribute_value,
                    trend_status,
                ),
                "reason": build_trend_reason(
                    signal.attribute_type,
                    signal.attribute_value,
                    trend_status,
                ),
                "attribute_type": signal.attribute_type,
                "attribute_value": signal.attribute_value,
                "trend_score": features["trend_score"],
                "growth_rate": features["growth_rate"],
                "trend_status": trend_status,
                "confidence": round(confidence, 4),
                "display_badge": get_display_badge(trend_status),
            }
        )

    return {
        "total_insights": len(insights),
        "insights": insights,
    }

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db
from app.core.constants import is_safe_user_facing_trend
from app.services.trend_analysis_service import calculate_trend_signals

router = APIRouter(tags=["Trends Analysis & Signals"])


@router.get("/trends/analyze")
def analyze_trends(db: Session = Depends(get_db)):
    observations = db.query(models.TrendObservation).all()

    if not observations:
        raise HTTPException(
            status_code=404,
            detail="No trend observations found. Add trend observations first.",
        )

    latest_date = max(obs.collected_at for obs in observations)

    current_start = latest_date - timedelta(days=7)
    current_end = latest_date

    previous_start = current_start - timedelta(days=7)
    previous_end = current_start

    analyzed_results, meta = calculate_trend_signals(
        observations, current_start, current_end, previous_start, previous_end
    )

    if not analyzed_results:
        raise HTTPException(
            status_code=404,
            detail="No observations found in current or previous analysis windows.",
        )

    # Wipe ALL prior "weekly" rows, not just an exact start/end match — every
    # consumer only ever reads the single latest window, so an older window
    # left behind by a previous run is pure staleness (see the identical fix
    # and rationale in app/pipeline/compute_trend_signals.py).
    db.query(models.TrendSignal).filter(
        models.TrendSignal.time_window == "weekly",
    ).delete(synchronize_session=False)

    for item in analyzed_results:
        new_signal = models.TrendSignal(
            attribute_type=item["attribute_type"],
            attribute_value=item["attribute_value"],
            trend_score=item["trend_score"],
            growth_rate=item["growth_rate"],
            time_window=item["time_window"],
            start_date=item["start_date"],
            end_date=item["end_date"],
        )
        db.add(new_signal)

    db.commit()

    filtered_results = [
        item
        for item in analyzed_results
        if is_safe_user_facing_trend(item["attribute_type"], item["attribute_value"])
    ]

    return {
        "message": "Trend analysis completed successfully",
        "total_raw_trends_analyzed": len(analyzed_results),
        "total_trends_analyzed": len(filtered_results),
        "formula": meta["formula"],
        "current_period": meta["current_period"],
        "previous_period": meta["previous_period"],
        "trends": filtered_results,
    }


@router.get("/trends")
def get_all_trends(db: Session = Depends(get_db)):
    # Excludes attribute_type="joint_forecast" rows (written by
    # app/pipeline/joint_trend_forecast.py with time_window="weekly_forecast"
    # and end_date=now() at persist time). Those rows use a completely
    # different schema — trend_score there is a raw predicted count-delta,
    # not the normalized 0-1 score this endpoint's consumers expect — and
    # since they're persisted later in the same pipeline run, their end_date
    # would otherwise always outrank the real "weekly" window here.
    latest_trend = (
        db.query(models.TrendSignal)
        .filter(models.TrendSignal.time_window == "weekly")
        .order_by(models.TrendSignal.end_date.desc())
        .first()
    )

    if not latest_trend:
        return {
            "total_trends": 0,
            "trends": [],
        }

    all_trends = (
        db.query(models.TrendSignal)
        .filter(
            models.TrendSignal.time_window == latest_trend.time_window,
            models.TrendSignal.start_date == latest_trend.start_date,
            models.TrendSignal.end_date == latest_trend.end_date,
        )
        .order_by(models.TrendSignal.trend_score.desc())
        .all()
    )

    filtered_trends = [
        trend
        for trend in all_trends
        if is_safe_user_facing_trend(trend.attribute_type, trend.attribute_value)
    ]

    return {
        "time_window": latest_trend.time_window,
        "start_date": latest_trend.start_date,
        "end_date": latest_trend.end_date,
        "total_trends": len(filtered_trends),
        "trends": filtered_trends,
    }


@router.get("/trends/history")
def get_trend_history(db: Session = Depends(get_db)):
    # Excludes joint_forecast rows — see the comment in get_all_trends() above.
    all_trends = (
        db.query(models.TrendSignal)
        .filter(models.TrendSignal.time_window == "weekly")
        .order_by(
            models.TrendSignal.end_date.desc(),
            models.TrendSignal.trend_score.desc(),
        )
        .all()
    )

    filtered_trends = [
        trend
        for trend in all_trends
        if is_safe_user_facing_trend(trend.attribute_type, trend.attribute_value)
    ]

    return {
        "total_trends": len(filtered_trends),
        "trends": filtered_trends,
    }


@router.get("/trends/{attribute_type}")
def get_trends_by_attribute_type(
    attribute_type: str,
    db: Session = Depends(get_db),
):
    # Excludes joint_forecast rows — see the comment in get_all_trends() above.
    latest_trend = (
        db.query(models.TrendSignal)
        .filter(models.TrendSignal.time_window == "weekly")
        .order_by(models.TrendSignal.end_date.desc())
        .first()
    )

    if not latest_trend:
        raise HTTPException(
            status_code=404,
            detail="No trend data found",
        )

    all_trends = (
        db.query(models.TrendSignal)
        .filter(
            models.TrendSignal.attribute_type == attribute_type.lower(),
            models.TrendSignal.time_window == latest_trend.time_window,
            models.TrendSignal.start_date == latest_trend.start_date,
            models.TrendSignal.end_date == latest_trend.end_date,
        )
        .order_by(models.TrendSignal.trend_score.desc())
        .all()
    )

    filtered_trends = [
        trend
        for trend in all_trends
        if is_safe_user_facing_trend(trend.attribute_type, trend.attribute_value)
    ]

    if not filtered_trends:
        raise HTTPException(
            status_code=404,
            detail=f"No safe latest trends found for attribute_type: {attribute_type}",
        )

    return {
        "attribute_type": attribute_type.lower(),
        "time_window": latest_trend.time_window,
        "start_date": latest_trend.start_date,
        "end_date": latest_trend.end_date,
        "total_trends": len(filtered_trends),
        "trends": filtered_trends,
    }

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.trend import TrendHistoryPoint, TrendMetaResponse, TrendScoreOut
from app.services.trend_service import TrendService

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.get("")
def get_trends(
    horizon: int = Query(3, description="3 | 5"),
    min_confidence: str | None = Query(None),
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Straight indexed read from the latest trend_snapshots row — the model
    never runs inside a request (architecture spec §4.1)."""
    by_type = TrendService(db).get_trends(horizon=horizon, min_confidence=min_confidence, limit=limit)
    data = {
        attr_type: [TrendScoreOut.model_validate(r, from_attributes=True) for r in rows]
        for attr_type, rows in by_type.items()
    }
    return {"data": data, "meta": {"horizon": horizon}}


@router.get("/meta")
def get_meta(horizon: int = Query(3), db: Session = Depends(get_db)):
    snapshot = TrendService(db).get_meta(horizon=horizon)
    if not snapshot:
        return {"data": None}
    return {"data": TrendMetaResponse.model_validate(snapshot, from_attributes=True)}


@router.get("/history/{attr_type}/{attr_value}")
def get_history(
    attr_type: str, attr_value: str,
    horizon: int = Query(3), days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    rows = TrendService(db).get_history(attr_type, attr_value, horizon=horizon, days=days)
    data = [
        TrendHistoryPoint(
            as_of_date=snap.as_of_date, score=score.score,
            share_pct=score.share_pct, rank_in_type=score.rank_in_type,
        )
        for snap, score in rows
    ]
    return {"data": data, "meta": {"total": len(data)}}


@router.get("/{attr_type}")
def get_trends_for_type(
    attr_type: str, limit: int = Query(10, ge=1, le=100),
    horizon: int = Query(3), db: Session = Depends(get_db),
):
    rows = TrendService(db).get_trends_for_type(attr_type, horizon=horizon, limit=limit)
    data = [TrendScoreOut.model_validate(r, from_attributes=True) for r in rows]
    return {"data": data, "meta": {"total": len(data)}}

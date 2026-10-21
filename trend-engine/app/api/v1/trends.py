from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import AfterValidator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AttrType
from app.schemas.trend import (
    ProductTrendOut, ScoreProductsRequest, SegmentScoreOut, TrendHistoryPoint, TrendingProductOut, TrendMetaResponse,
    TrendScoreOut,
)
from app.services.trend_service import TrendService

# Only these horizons are ever computed; anything else used to fail later as a misleading 503.


def _supported_horizon(value: int) -> int:
    # A Literal[3, 5] would reject the string "3" that arrives in a URL, so check after int parsing.
    if value not in (3, 5):
        raise ValueError("horizon must be 3 or 5")
    return value


Horizon = Annotated[int, Query(description="3 | 5"), AfterValidator(_supported_horizon)]
Confidence = Literal["high", "medium", "low"]

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.post("/score-products")
def score_products_endpoint(body: ScoreProductsRequest, db: Session = Depends(get_db)):
    """Trend score for products the caller owns. Stateless: nothing from the request is stored."""
    results, meta = TrendService(db).score_partner_products(
        [p.model_dump() for p in body.products], horizon=body.horizon
    )
    return {"data": [ProductTrendOut.model_validate(r) for r in results], "meta": meta}


@router.get("/products")
def get_trending_products(
    horizon: Horizon = 3,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    rows = TrendService(db).get_trending_products(horizon=horizon, limit=limit)
    products = [TrendingProductOut.model_validate(r) for r in rows]
    return {"products": products, "meta": {"total": len(products)}}


@router.get("")
def get_trends(
    horizon: Horizon = 3,
    min_confidence: Confidence | None = Query(None),
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    by_type = TrendService(db).get_trends(horizon=horizon, min_confidence=min_confidence, limit=limit)
    data = {
        attr_type: [TrendScoreOut.model_validate(r, from_attributes=True) for r in rows]
        for attr_type, rows in by_type.items()
    }
    return {"data": data, "meta": {"horizon": horizon}}


@router.get("/segments")
def get_segment_trends(
    horizon: Horizon = 3,
    min_confidence: Confidence | None = Query(None),
    segment_type: str | None = Query(None, description="e.g. color_x_category"),
    rising_only: bool = Query(True),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Attribute combinations ("white + dress") ranked by trend score, strongest first."""
    snapshot, rows = TrendService(db).get_segment_trends(
        horizon=horizon, segment_type=segment_type, min_confidence=min_confidence,
        rising_only=rising_only, limit=limit,
    )
    data = [
        SegmentScoreOut(
            segment_type=r.segment_type, segment=r.segment_value,
            parts=[
                {"attr_type": r.part1_type, "attr_value": r.part1_value},
                {"attr_type": r.part2_type, "attr_value": r.part2_value},
            ],
            rank_in_type=r.rank_in_type, score=r.score, share_pct=r.share_pct,
            share_change_pct=r.share_change_pct, stores_carrying=r.stores_carrying,
            confidence=r.confidence, lifecycle_stage=r.lifecycle_stage,
        )
        for r in rows
    ]
    return {"data": data, "meta": {"horizon": horizon, "as_of_date": str(snapshot.as_of_date), "count": len(data)}}


@router.get("/meta")
def get_meta(horizon: Horizon = 3, db: Session = Depends(get_db)):
    snapshot = TrendService(db).get_meta(horizon=horizon)
    if not snapshot:
        return {"data": None}
    return {"data": TrendMetaResponse.model_validate(snapshot, from_attributes=True)}


@router.get("/history/{attr_type}/{attr_value}")
def get_history(
    attr_type: AttrType, attr_value: str,
    horizon: Horizon = 3, days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    rows = TrendService(db).get_history(attr_type.value, attr_value, horizon=horizon, days=days)
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
    attr_type: AttrType, limit: int = Query(10, ge=1, le=100),
    horizon: Horizon = 3, db: Session = Depends(get_db),
):
    rows = TrendService(db).get_trends_for_type(attr_type.value, horizon=horizon, limit=limit)
    data = [TrendScoreOut.model_validate(r, from_attributes=True) for r in rows]
    return {"data": data, "meta": {"total": len(data)}}

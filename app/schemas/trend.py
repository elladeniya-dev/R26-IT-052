from datetime import date, datetime

from pydantic import BaseModel


class TrendScoreOut(BaseModel):
    attr_type: str
    attr_value: str
    rank_in_type: int
    score: float
    share_pct: float | None
    share_change_pct: float | None
    restock_rate: float | None
    disappear_rate: float | None
    breadth: float | None
    stores_carrying: int | None
    confidence: str | None
    lifecycle_stage: str | None
    mk_p: float | None


class TrendsResponse(BaseModel):
    category: list[TrendScoreOut] = []
    color: list[TrendScoreOut] = []
    pattern: list[TrendScoreOut] = []
    fabric: list[TrendScoreOut] = []
    sleeve_length: list[TrendScoreOut] = []
    garment_length: list[TrendScoreOut] = []
    neckline: list[TrendScoreOut] = []
    style_detail: list[TrendScoreOut] = []


class TrendHistoryPoint(BaseModel):
    as_of_date: date
    score: float
    share_pct: float | None
    rank_in_type: int


class TrendMetaResponse(BaseModel):
    model_name: str
    model_ic: float | None
    as_of_date: date
    horizon_days: int
    window_days: int
    computed_at: datetime

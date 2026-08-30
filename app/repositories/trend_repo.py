from sqlalchemy import select

from app.models import TrendScore, TrendSnapshot
from app.repositories.base import BaseRepository


class TrendRepository(BaseRepository):
    def get_latest_snapshot(self, horizon_days: int = 3) -> TrendSnapshot | None:
        stmt = (
            select(TrendSnapshot)
            .where(TrendSnapshot.horizon_days == horizon_days)
            .order_by(TrendSnapshot.as_of_date.desc(), TrendSnapshot.computed_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_scores(
        self, snapshot_id: int, attr_type: str | None = None, min_confidence: str | None = None,
        limit: int | None = None,
    ) -> list[TrendScore]:
        stmt = select(TrendScore).where(TrendScore.snapshot_id == snapshot_id)
        if attr_type:
            stmt = stmt.where(TrendScore.attr_type == attr_type)
        if min_confidence:
            order = {"low": 0, "medium": 1, "high": 2}
            allowed = [k for k, v in order.items() if v >= order.get(min_confidence, 0)]
            stmt = stmt.where(TrendScore.confidence.in_(allowed))
        stmt = stmt.order_by(TrendScore.attr_type, TrendScore.rank_in_type)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_history(
        self, attr_type: str, attr_value: str, horizon_days: int = 3, days: int = 30
    ) -> list[tuple[TrendSnapshot, TrendScore]]:
        stmt = (
            select(TrendSnapshot, TrendScore)
            .join(TrendScore, TrendScore.snapshot_id == TrendSnapshot.snapshot_id)
            .where(
                TrendSnapshot.horizon_days == horizon_days,
                TrendScore.attr_type == attr_type,
                TrendScore.attr_value == attr_value,
            )
            .order_by(TrendSnapshot.as_of_date.desc())
            .limit(days)
        )
        return list(self.db.execute(stmt).all())

    def save_snapshot(
        self, *, as_of_date, horizon_days: int, model_name: str, model_ic: float | None,
        window_days: int, scores: list[dict],
    ) -> TrendSnapshot:
        snapshot = TrendSnapshot(
            as_of_date=as_of_date, horizon_days=horizon_days, model_name=model_name,
            model_ic=model_ic, window_days=window_days,
        )
        self.db.add(snapshot)
        self.db.flush()  # populate snapshot.snapshot_id

        by_type: dict[str, list[dict]] = {}
        for s in scores:
            by_type.setdefault(s["attr_type"], []).append(s)
        for attr_type, rows in by_type.items():
            rows.sort(key=lambda r: r["score"], reverse=True)
            for rank, r in enumerate(rows, start=1):
                self.db.add(TrendScore(
                    snapshot_id=snapshot.snapshot_id,
                    attr_type=attr_type,
                    attr_value=r["attribute"],
                    rank_in_type=rank,
                    score=r["score"],
                    share_pct=r.get("share_pct"),
                    share_change_pct=r.get("share_change_pct"),
                    restock_rate=r.get("restock_rate"),
                    disappear_rate=r.get("disappear_rate"),
                    breadth=r.get("breadth"),
                    stores_carrying=r.get("stores_carrying"),
                    confidence=r.get("confidence"),
                    lifecycle_stage=r.get("stage"),
                    mk_p=r.get("mk_p"),
                ))
        self.db.commit()
        return snapshot

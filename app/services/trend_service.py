from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import StaleSnapshotError
from app.ml.engine import TrendEngine
from app.models import TrendSnapshot
from app.repositories.observation_repo import ObservationRepository
from app.repositories.trend_repo import TrendRepository

HORIZONS = (3, 5)


class TrendService:
    """Owns the trend business rules. The API never scores inside a request
    (architecture spec §4.1) — compute_snapshot() is called only from
    jobs/compute_trends.py; every read-path method here is a plain indexed
    query against the last persisted snapshot."""

    def __init__(self, db: Session, engine: TrendEngine | None = None):
        self.db = db
        self.trend_repo = TrendRepository(db)
        self.obs_repo = ObservationRepository(db)
        self.engine = engine or TrendEngine()

    def compute_snapshot(self, horizon_days: int, as_of: date | None = None) -> dict:
        attrs_long, presence = self.obs_repo.build_ml_panel_inputs()
        if presence.empty:
            raise StaleSnapshotError("No observations to score yet")

        results = self.engine.rank(attrs_long, presence, top_k=None, horizon=horizon_days)
        as_of_date = as_of or presence.date.max().date()
        snapshot = self.trend_repo.save_snapshot(
            as_of_date=as_of_date,
            horizon_days=horizon_days,
            model_name=self.engine.model_name,
            model_ic=self.engine.model_ic,
            window_days=self.engine.window,
            scores=results,
        )
        return {"snapshot_id": snapshot.snapshot_id, "n_scored": len(results)}

    def get_trends(
        self, horizon: int = 3, min_confidence: str | None = None, limit: int = 5
    ) -> dict[str, list]:
        snapshot = self.trend_repo.get_latest_snapshot(horizon)
        if not snapshot:
            raise StaleSnapshotError("No trend snapshot computed yet — run jobs/compute_trends.py")

        scores = self.trend_repo.get_scores(snapshot.snapshot_id, min_confidence=min_confidence)
        out: dict[str, list] = {}
        for s in scores:
            out.setdefault(s.attr_type.value, []).append(s)
        return {k: v[:limit] for k, v in out.items()}

    def get_trends_for_type(
        self, attr_type: str, horizon: int = 3, limit: int = 10
    ) -> list:
        snapshot = self.trend_repo.get_latest_snapshot(horizon)
        if not snapshot:
            raise StaleSnapshotError("No trend snapshot computed yet — run jobs/compute_trends.py")
        return self.trend_repo.get_scores(snapshot.snapshot_id, attr_type=attr_type, limit=limit)

    def get_history(self, attr_type: str, attr_value: str, horizon: int = 3, days: int = 30) -> list:
        return self.trend_repo.get_history(attr_type, attr_value, horizon, days)

    def get_meta(self, horizon: int = 3) -> TrendSnapshot | None:
        return self.trend_repo.get_latest_snapshot(horizon)

from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.core.exceptions import StaleSnapshotError
from app.ml.engine import TrendEngine
from app.models import TrendSnapshot
from app.repositories.observation_repo import ObservationRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.trend_repo import TrendRepository

HORIZONS = (3, 5)
PRODUCT_FEED_ATTR_TYPES = ("category", "color")
MIN_STORES_FOR_FEED = 5  # a trend carried by only a couple of stores is not corroborated


class TrendService:
    def __init__(self, db: Session, engine: TrendEngine | None = None):
        self.db = db
        self.trend_repo = TrendRepository(db)
        self.obs_repo = ObservationRepository(db)
        self.product_repo = ProductRepository(db)
        self._engine = engine  # lazy — see engine property below

    @property
    def engine(self) -> TrendEngine:
        if self._engine is None:
            self._engine = TrendEngine()
        return self._engine

    def compute_snapshot(self, horizon_days: int, as_of: date | None = None) -> dict:
        attrs_long, presence = self.obs_repo.build_ml_panel_inputs()
        if presence.empty:
            raise StaleSnapshotError("No observations to score yet")

        results = self.engine.rank(attrs_long, presence, top_k=None, horizon=horizon_days)
        as_of_date = as_of or pd.to_datetime(presence.date).max().date()
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

    def get_trending_products(self, horizon: int = 3, limit: int = 20) -> list[dict]:
        """Attribute trend scores, resolved to real still-listed products for the app's feed."""
        snapshot = self.trend_repo.get_latest_snapshot(horizon)
        if not snapshot:
            raise StaleSnapshotError("No trend snapshot computed yet — run jobs/compute_trends.py")

        scores = self.trend_repo.get_scores(snapshot.snapshot_id)
        rising = sorted(
            (
                s for s in scores
                if s.attr_type.value in PRODUCT_FEED_ATTR_TYPES and s.score > 0
                and (s.stores_carrying or 0) >= MIN_STORES_FOR_FEED
            ),
            key=lambda s: s.score, reverse=True,
        )

        # Round-robin across the rising attributes so one attribute can't fill the feed,
        # and cap each brand so one store can't either.
        pools = [
            (s, self.product_repo.get_product_ids_for_attribute(s.attr_type.value, s.attr_value, limit=8))
            for s in rising[:12]
        ]
        brand_cap = max(2, limit // 4)
        brand_count: dict[str, int] = {}
        best_score: dict = {}
        for depth in range(8):
            for s, ids in pools:
                if depth >= len(ids) or len(best_score) >= limit:
                    continue
                pid = ids[depth]
                brand = pid.split(":")[0]
                if pid in best_score or brand_count.get(brand, 0) >= brand_cap:
                    continue
                best_score[pid] = s
                brand_count[brand] = brand_count.get(brand, 0) + 1

        top_ids = sorted(best_score, key=lambda pid: best_score[pid].score, reverse=True)[:limit]
        if not top_ids:
            return []

        products = self.product_repo.get_products_bulk(top_ids)
        lifecycles = self.product_repo.get_lifecycles_bulk(top_ids)
        attrs = self.product_repo.get_attributes_bulk(top_ids, ("color", "style_detail"))
        brands = self.product_repo.get_brands_bulk({p.brand_id for p in products.values()})

        out = []
        for pid in top_ids:
            product = products.get(pid)
            if not product:
                continue
            lifecycle = lifecycles.get(pid)
            brand = brands.get(product.brand_id)
            score = best_score[pid]
            out.append({
                "item_id": pid,
                "title": product.title,
                "category": product.category,
                "color": attrs.get(pid, {}).get("color", []),
                "style": attrs.get(pid, {}).get("style_detail", []),
                "brand": brand.display_name if brand else "",
                "source": brand.slug if brand else "",
                "price": float(lifecycle.price_last_lkr) if lifecycle and lifecycle.price_last_lkr else 0.0,
                "image_url": product.image_url or "",
                "product_url": product.product_url or "",
                "trend_score": float(score.score),
                "trend_reason": f"{score.attr_value.title()} {score.attr_type.value} is trending up",
            })
        return out

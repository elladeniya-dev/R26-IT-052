"""
Trending tab — deliberately separate from recommendation_service.py and never
imports from it. No user preferences, no scoring formula: just Koji products
whose category or color is currently flagged rising in our own TrendSignal
data. Reuses the same taxonomy standardization (map_category/map_color) and
the same RISING_THRESHOLD definition of "rising" the rest of the app uses,
so "trending" means the same thing everywhere in the system.
"""
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.koji_database import KojiProduct
from app.models import TrendSignal
from app.pipeline.local_taxonomy_mapper import map_category, map_color
from app.pipeline.trend_shape_template import RISING_THRESHOLD

# Obviously-fake placeholder rows seeded for testing — not real inventory.
_EXCLUDED_KOJI_SOURCES = {"sample_data", "sample_crawler"}


def _load_rising_signals(db: Session, attribute_type: str) -> Dict[str, float]:
    rows = (
        db.query(TrendSignal.attribute_value, func.max(TrendSignal.trend_score))
        .filter(
            TrendSignal.time_window == "weekly",
            TrendSignal.attribute_type == attribute_type,
            TrendSignal.trend_score >= RISING_THRESHOLD,
        )
        .group_by(TrendSignal.attribute_value)
        .all()
    )
    return {value: score for value, score in rows}


def get_trending_products(db: Session, koji_db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    rising_categories = _load_rising_signals(db, "category")
    rising_colors = _load_rising_signals(db, "color")

    candidates = (
        koji_db.query(KojiProduct)
        .filter(
            KojiProduct.availability.is_(True),
            ~KojiProduct.source.in_(_EXCLUDED_KOJI_SOURCES),
        )
        .all()
    )

    results = []
    for product in candidates:
        mapped_category = map_category(product.category).lower()
        mapped_colors = [map_color(c).lower() for c in (product.color or [])]

        category_score = rising_categories.get(mapped_category)
        color_matches = [(c, rising_colors[c]) for c in mapped_colors if c in rising_colors]

        if category_score is None and not color_matches:
            continue

        best_score = category_score or 0.0
        reason = f"Trending category: {product.category}" if category_score else ""
        if color_matches:
            best_color, best_color_score = max(color_matches, key=lambda cs: cs[1])
            if best_color_score > best_score:
                best_score = best_color_score
                reason = f"Trending color: {best_color}"

        results.append({
            "item_id": product.item_id,
            "title": product.title or "",
            "category": product.category or "",
            "color": product.color or [],
            "style": product.style or [],
            "brand": product.brand or "",
            "source": product.source or "",
            "price": float(product.price or 0),
            "image_url": product.image_url or "",
            "product_url": product.product_url or "",
            "trend_score": round(best_score, 4),
            "trend_reason": reason,
        })

    results.sort(key=lambda r: r["trend_score"], reverse=True)
    return results[:limit]

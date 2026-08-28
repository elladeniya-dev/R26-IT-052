"""
Matches a user's style preferences against the Koji product catalog (a
teammate's separate, live database — see app/core/koji_database.py), ranked
by three real, independently-computed signals:

  user_match_score    — overlap with the user's stated preferences
                         (category, color, style, brand)
  ml_similarity_score — how much this product's category/color align with
                         what our own trend engine currently flags as rising
                         (real TrendSignal data, same source /trends serves)
  product_quality_score — listing completeness (real image, description,
                         plausible price) — there's no reviews/ratings data
                         for either catalog, so this deliberately measures
                         something real rather than fabricating a rating.

final_score = 0.40 * user_match_score + 0.35 * ml_similarity_score
              + 0.25 * product_quality_score

Category/color are standardized through the same map_category()/map_color()
functions the ETL pipeline uses, on both the user's preferences and the
Koji product, so synonyms (e.g. "navy" vs "blue") land in the same bucket
instead of needing a second, separate matching vocabulary.
"""
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.koji_database import KojiProduct
from app.models import TrendSignal
from app.pipeline.local_taxonomy_mapper import map_category, map_color

# Obviously-fake placeholder rows seeded for testing — not real inventory.
_EXCLUDED_KOJI_SOURCES = {"sample_data", "sample_crawler"}

_WEIGHTS = {"user_match": 0.40, "ml_similarity": 0.35, "quality": 0.25}


def _fetch_candidates(koji_db: Session, price_min: float, price_max: float) -> List[KojiProduct]:
    return (
        koji_db.query(KojiProduct)
        .filter(
            KojiProduct.availability.is_(True),
            KojiProduct.price >= price_min,
            KojiProduct.price <= price_max,
            ~KojiProduct.source.in_(_EXCLUDED_KOJI_SOURCES),
        )
        .all()
    )


def _score_user_match(
    product: KojiProduct,
    mapped_category: str,
    mapped_colors: List[str],
    preferred_categories: List[str],
    preferred_colors: List[str],
    preferred_styles: List[str],
    preferred_brands: List[str],
) -> tuple[float, List[str]]:
    tags: List[str] = []

    category_hit = False
    if preferred_categories:
        mapped_prefs = {map_category(c) for c in preferred_categories}
        category_hit = mapped_category in mapped_prefs
        if category_hit:
            tags.append(f"Matches your preferred category: {mapped_category}")
    category_score = 1.0 if category_hit or not preferred_categories else 0.0

    color_score = 1.0
    if preferred_colors:
        mapped_prefs = {map_color(c) for c in preferred_colors}
        matched = mapped_prefs & set(mapped_colors)
        color_score = 1.0 if matched else 0.0
        if matched:
            tags.append(f"Available in a color you like: {next(iter(matched))}")

    style_score = 1.0
    product_styles = {str(s).strip().lower() for s in (product.style or [])}
    if preferred_styles:
        matched_styles = {s.strip().lower() for s in preferred_styles} & product_styles
        style_score = 1.0 if matched_styles else 0.0
        if matched_styles:
            tags.append(f"Matches your style: {next(iter(matched_styles)).title()}")

    brand_score = 1.0
    if preferred_brands:
        brand_score = 1.0 if (product.brand or "").strip().lower() in {
            b.strip().lower() for b in preferred_brands
        } else 0.0
        if brand_score:
            tags.append(f"From a brand you follow: {product.brand}")

    score = (
        0.35 * category_score + 0.25 * color_score + 0.25 * style_score + 0.15 * brand_score
    )
    return round(score, 4), tags


def _score_trend_alignment(
    db: Session, mapped_category: str, mapped_colors: List[str]
) -> tuple[float, List[str]]:
    tags: List[str] = []
    scores: List[float] = []

    category_signal = (
        db.query(func.max(TrendSignal.trend_score))
        .filter(
            TrendSignal.time_window == "weekly",
            TrendSignal.attribute_type == "category",
            TrendSignal.attribute_value == mapped_category.lower(),
        )
        .scalar()
    )
    if category_signal is not None:
        scores.append(category_signal)
        if category_signal >= 0.55:
            tags.append(f"Currently a trending category (score {category_signal:.2f})")

    if mapped_colors:
        color_signal = (
            db.query(func.max(TrendSignal.trend_score))
            .filter(
                TrendSignal.time_window == "weekly",
                TrendSignal.attribute_type == "color",
                TrendSignal.attribute_value.in_([c.lower() for c in mapped_colors]),
            )
            .scalar()
        )
        if color_signal is not None:
            scores.append(color_signal)
            if color_signal >= 0.55:
                tags.append(f"Trending color right now (score {color_signal:.2f})")

    score = round(sum(scores) / len(scores), 4) if scores else 0.0
    return score, tags


def _score_quality(product: KojiProduct) -> float:
    has_real_image = bool(product.image_url) and product.image_url.startswith("http") and (
        "example.com" not in product.image_url
    )
    has_description = bool(product.description) and len(product.description.strip()) > 10
    plausible_price = product.price is not None and 100 <= product.price <= 200000

    score = 0.0
    if has_real_image:
        score += 0.4
    if has_description:
        score += 0.3
    if plausible_price:
        score += 0.3
    return round(score, 4)


def get_recommendations(
    db: Session,
    koji_db: Session,
    preferred_categories: List[str],
    preferred_colors: List[str],
    preferred_styles: List[str],
    preferred_brands: List[str],
    price_min: float,
    price_max: float,
    max_results: int,
) -> List[Dict[str, Any]]:
    candidates = _fetch_candidates(koji_db, price_min, price_max)

    results = []
    for product in candidates:
        mapped_category = map_category(product.category)
        raw_colors = product.color or []
        mapped_colors = [map_color(c) for c in raw_colors]

        user_match_score, user_tags = _score_user_match(
            product, mapped_category, mapped_colors,
            preferred_categories, preferred_colors, preferred_styles, preferred_brands,
        )
        ml_similarity_score, trend_tags = _score_trend_alignment(db, mapped_category, mapped_colors)
        quality_score = _score_quality(product)

        final_score = round(
            _WEIGHTS["user_match"] * user_match_score
            + _WEIGHTS["ml_similarity"] * ml_similarity_score
            + _WEIGHTS["quality"] * quality_score,
            4,
        )

        results.append({
            "item_id": product.item_id,
            "title": product.title or "",
            "category": product.category or "",
            "color": raw_colors,
            "style": product.style or [],
            "brand": product.brand or "",
            "source": product.source or "",
            "price": float(product.price or 0),
            "image_url": product.image_url or "",
            "product_url": product.product_url or "",
            "final_score": final_score,
            "user_match_score": user_match_score,
            "ml_similarity_score": ml_similarity_score,
            "product_quality_score": quality_score,
            "reason_tags": user_tags + trend_tags,
        })

    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results[:max_results]

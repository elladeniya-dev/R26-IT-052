import logging
from typing import List, Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def get_grounded_attributes(top_category: str, transactions: pd.DataFrame,
                             attribute_col: str, lookback_weeks: int = 8,
                             decay_rate: float = 0.15, top_n: int = 3):
    """Given a trending category, find colors/patterns that actually
    co-occur with it historically — not just whatever's globally popular."""

    if transactions.empty:
        return pd.Series(dtype=float)

    max_date = transactions['t_dat'].max()
    cutoff = max_date - pd.Timedelta(weeks=lookback_weeks)

    cat_txns = transactions[
        (transactions['product_type_name'] == top_category) &
        (transactions['t_dat'] >= cutoff)
    ].copy()

    if cat_txns.empty:
        return pd.Series(dtype=float)

    # recency weighting — recent purchases count more
    cat_txns['weight'] = np.exp(
        -decay_rate * (max_date - cat_txns['t_dat']).dt.days / 7
    )

    # P(attribute | category) — weighted
    p_attr_given_cat = cat_txns.groupby(attribute_col)['weight'].sum()
    p_attr_given_cat /= p_attr_given_cat.sum()

    # P(attribute) overall — global baseline, unweighted, full dataset
    p_attr_global = transactions[attribute_col].value_counts(normalize=True)

    # lift = how much more likely this attribute is WITH this category
    # vs. on its own — filters out "black is just always popular"
    lift = (p_attr_given_cat / p_attr_global.reindex(p_attr_given_cat.index)).dropna()
    lift = lift[lift > 1.0]  # only keep genuinely associated attributes

    # rank survivors by their actual weighted share within the category
    ranked = p_attr_given_cat.loc[lift.index].sort_values(ascending=False)
    return ranked.head(top_n)


def get_top_forecast_categories(db, top_k: int = 1) -> List[Dict[str, Any]]:
    """
    Reads real joint-attribute forecasts (category|color|pattern, produced by
    scripts/joint_trend_forecast.py — a LightGBM model trained on H&M's
    transaction history, run against our own daily Sri Lankan scrape data)
    from TrendSignal. Returns [] honestly if none exist yet — this happens
    when there isn't enough real history (the methodology requires >= 6 weeks
    per attribute combination before it will forecast one at all).
    """
    from app.models import TrendSignal

    rows = (
        db.query(TrendSignal)
        .filter(TrendSignal.attribute_type == "joint_forecast")
        .order_by(TrendSignal.trend_score.desc())
        .limit(top_k)
        .all()
    )

    results = []
    for row in rows:
        parts = row.attribute_value.split("|")
        category = parts[0] if parts else row.attribute_value
        results.append({
            "category": category,
            "joint_key": row.attribute_value,
            "predicted_change": row.trend_score,
            "growth_rate": row.growth_rate,
        })
    return results


class TrendMLPredictionService:
    def predict_trend_label(self, trend_score: float, **kwargs) -> Dict[str, Any]:
        """
        Classifies a trend_score (already computed by the Laplace-smoothed
        growth/count/rank formula in trend_analysis_service.py) into
        rising/stable/weak using fixed, explainable thresholds — deliberately
        rule-based rather than a second opaque model. trend_score is already
        a validated metric; stacking an unexplainable classifier on top of it
        would add complexity without adding trustworthiness.
        """
        if trend_score >= 0.55:
            label = "rising"
        elif trend_score >= 0.35:
            label = "stable"
        else:
            label = "weak"

        # Confidence = distance from the nearest threshold, normalized to
        # [0.5, 1.0] — a score right at a boundary is a coin flip, a score
        # deep inside a bucket is confident.
        boundaries = [0.35, 0.55]
        dist_to_boundary = min(abs(trend_score - b) for b in boundaries)
        confidence = round(min(1.0, 0.5 + dist_to_boundary), 4)

        scores = {"rising": 0.0, "stable": 0.0, "weak": 0.0}
        scores[label] = confidence
        remainder = round(1.0 - confidence, 4)
        others = [l for l in scores if l != label]
        for o in others:
            scores[o] = round(remainder / len(others), 4)

        return {
            "predicted_trend_label": label,
            "confidence_scores": scores,
            "model_type": "Threshold classifier on Laplace-smoothed trend_score",
        }


    def _fetch_live_transactions(self) -> pd.DataFrame:
        """
        Fetches live inventory data from the Neon PostgreSQL database
        to calculate Lift co-occurrences against the actual market.
        """
        from app.core.database import SessionLocal
        from app.models import Product

        db = SessionLocal()
        try:
            # Look back 12 weeks to capture enough data for Lift
            cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(weeks=12)
            # Use raw datetimes since Product.collected_at is naive or aware depending on DB driver
            cutoff_dt = cutoff.replace(tzinfo=None)

            products = db.query(Product).filter(Product.collected_at >= cutoff_dt).all()

            # Use the ML-standardized taxonomy fields (ml_category/ml_color/
            # ml_pattern), not the raw scraped ones — the forecast categories
            # this gets joined against (in get_grounded_attributes) are also
            # taxonomy-standardized, and the raw fields carry through genuine
            # junk (size codes, price ranges, collection names) that isn't a
            # color or pattern at all.
            data = []
            for p in products:
                if not p.ml_category or p.ml_category == "Unknown":
                    continue
                data.append({
                    "t_dat": p.collected_at,
                    "product_type_name": p.ml_category,
                    "colour_group_name": p.ml_color or "Unknown",
                    "graphical_appearance_name": p.ml_pattern or "Solid"
                })

            if not data:
                return pd.DataFrame()

            return pd.DataFrame(data)
        finally:
            db.close()

    def predict_trending_outfit(self, transactions: pd.DataFrame = None, top_k_categories: int = 1) -> List[Dict[str, Any]]:
        """
        Real category source: LightGBM joint-attribute forecasts (see
        scripts/joint_trend_forecast.py), ranked by predicted_change.
        Grounding (which colors/patterns actually co-occur): lift-filtered
        analysis of our own live scraped inventory, not a global guess.
        Returns [] if no forecast is available yet (insufficient history) —
        never falls back to a hardcoded category.
        """
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            top_forecasts = get_top_forecast_categories(db, top_k=top_k_categories)
        finally:
            db.close()

        if not top_forecasts:
            logger.warning(
                "No joint-attribute forecasts available yet — attribute "
                "combinations need >= 6 weeks of real scrape history before "
                "this methodology will forecast them."
            )
            return []

        if transactions is None:
            transactions = self._fetch_live_transactions()
            if transactions.empty:
                logger.warning("Live database is empty. No transactions available for Lift calculation.")

        results = []
        for forecast in top_forecasts:
            category = forecast["category"]
            colors = get_grounded_attributes(category, transactions, 'colour_group_name')
            patterns = get_grounded_attributes(category, transactions, 'graphical_appearance_name')

            results.append({
                'category': category,
                'colors': colors.index.tolist() if not colors.empty else ["Unknown"],
                'patterns': patterns.index.tolist() if not patterns.empty else ["Unknown"],
                'predicted_change': forecast["predicted_change"],
                'model_type': 'Joint-Attribute LightGBM Forecast + Lift-Filtered Grounding (Live Data)',
            })

        return results


trend_ml_service = TrendMLPredictionService()

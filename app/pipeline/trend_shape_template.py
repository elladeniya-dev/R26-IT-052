"""
"Content doesn't transfer, shape might."

The joint-attribute LightGBM model (joint_trend_forecast.py) predicts next
week's count for attributes with >= 6 weeks of real SL history. This module
covers attributes that don't have that yet, but our own detector (the
Laplace-smoothed trend_score in trend_analysis_service.py) already flags as
rising right now: instead of learning WHAT is trending from H&M (wrong —
different market), it learns the SHAPE a real trend follows once it starts
rising — averaged from real historical rise events in H&M's transaction
history — and applies that generic shape as a multi-week projection to the
attribute's current real SL count.

No training, no model — just averaging real historical curves. Deliberately
reuses this project's ALREADY-VALIDATED "is it rising" definition
(trend_score >= RISING_THRESHOLD, the same one predict_trend_label uses) —
not a second, differently-defined detector. Two different answers to "is X
trending" depending which code path you ask would be a real inconsistency,
not just redundant code.
"""
import json
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

MIN_HISTORY = 3
BASELINE_WINDOW = 8
Z_THRESHOLD = 2.0       # only used when extracting curves from H&M's own history
CURVE_LENGTH = 5        # weeks captured after a rise starts
RISING_THRESHOLD = 0.55  # matches predict_trend_label's "rising" cutoff

TEMPLATE_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "trend_shape_template.json"


def load_template() -> Optional[np.ndarray]:
    """Loads the real averaged rise-shape template produced by
    train_joint_trend_model.py from actual H&M rise events. Returns None if
    it hasn't been generated yet — never fabricates a placeholder shape."""
    if not TEMPLATE_PATH.exists():
        return None
    with open(TEMPLATE_PATH) as f:
        data = json.load(f)
    return np.array(data["template"])


def _rolling_zscore(counts: np.ndarray, i: int) -> Optional[float]:
    """z-score of counts[i] against counts[:i]'s own history — used only to
    find real rise *events* inside H&M's history, not as our live SL
    trend definition (that's trend_score, computed elsewhere)."""
    if i < MIN_HISTORY:
        return None
    baseline = counts[max(0, i - BASELINE_WINDOW):i]
    mean, std = np.mean(baseline), np.std(baseline)
    return (counts[i] - mean) / std if std > 0.5 else float(counts[i] - mean)


def extract_rise_curves(weekly_df: pd.DataFrame) -> List[np.ndarray]:
    """
    weekly_df: columns = [attribute, week, count], H&M weekly counts.
    Finds each attribute's first real z-score-crossing rise, returns its
    normalized trajectory for the following CURVE_LENGTH weeks (divided by
    its own starting value, so every curve starts at 1.0 and is comparable
    across attributes regardless of scale). Only the first rise per
    attribute — a sustained multi-week rise would otherwise get captured
    many overlapping times, skewing the average toward the tail of a rise
    instead of a clean start-of-rise shape.
    """
    curves = []
    for attr, group in weekly_df.sort_values("week").groupby("attribute"):
        counts = group["count"].values
        for i in range(MIN_HISTORY, len(counts) - 1):
            z = _rolling_zscore(counts, i)
            if z is not None and z >= Z_THRESHOLD and counts[i] > 0:
                window = counts[i:i + CURVE_LENGTH]
                if len(window) >= 2:
                    curves.append(window / window[0])
                break
    return curves


def average_trend_curve(curves: List[np.ndarray]) -> np.ndarray:
    """Averages curves of different lengths week by week, ignoring weeks a
    shorter curve doesn't reach. The one generic 'what does a real rise
    typically look like' template, e.g. [1.0, 1.3, 1.6, 1.4, 1.1]."""
    max_len = max(len(c) for c in curves)
    padded = np.full((len(curves), max_len), np.nan)
    for i, c in enumerate(curves):
        padded[i, :len(c)] = c
    return np.nanmean(padded, axis=0)


def forecast_with_template(current_count: float, template: np.ndarray) -> np.ndarray:
    """Applies the generic H&M-derived shape to a currently-rising SL
    attribute's real current count."""
    return current_count * template


def get_rising_sl_attributes(db, threshold: float = RISING_THRESHOLD) -> List[dict]:
    """
    Our own already-validated 'is it rising' signal — the same trend_score
    predict_trend_label classifies as 'rising'. Deliberately NOT a separate
    z-score check against SL data; z-scoring is only used above, internally,
    to mine rise-shape examples out of H&M's history.

    TrendSignal doesn't persist the raw current-week count (only the derived
    trend_score/growth_rate), so it's re-summed here directly from
    TrendObservation — the actual source of truth for "how many mentions
    this week," not a stand-in value.
    """
    from sqlalchemy import func
    from app.models import TrendSignal, TrendObservation

    latest = (
        db.query(TrendSignal)
        .filter(TrendSignal.attribute_type != "joint_forecast")
        .order_by(TrendSignal.end_date.desc())
        .first()
    )
    if not latest:
        return []

    signals = (
        db.query(TrendSignal)
        .filter(
            TrendSignal.time_window == latest.time_window,
            TrendSignal.start_date == latest.start_date,
            TrendSignal.end_date == latest.end_date,
            TrendSignal.trend_score >= threshold,
            TrendSignal.attribute_type != "joint_forecast",
        )
        .order_by(TrendSignal.trend_score.desc())
        .all()
    )

    results = []
    for r in signals:
        current_count = (
            db.query(func.sum(TrendObservation.mention_count))
            .filter(
                TrendObservation.attribute_type == r.attribute_type,
                func.lower(TrendObservation.attribute_value) == r.attribute_value.lower(),
                TrendObservation.collected_at >= r.start_date,
                TrendObservation.collected_at <= r.end_date,
            )
            .scalar()
        ) or 0

        results.append({
            "attribute_type": r.attribute_type,
            "attribute_value": r.attribute_value,
            "trend_score": r.trend_score,
            "current_count": current_count,
        })
    return results


def run():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from app.core.database import SessionLocal

    template = load_template()
    if template is None:
        print("No shape template found — run scripts/train_joint_trend_model.py first.")
        return

    print(f"Loaded real H&M-derived rise template: {np.round(template, 3).tolist()}")

    db = SessionLocal()
    rising = get_rising_sl_attributes(db)
    db.close()

    print(f"\n{len(rising)} SL attributes currently flagged rising (trend_score >= {RISING_THRESHOLD}):\n")
    for attr in rising:
        projection = forecast_with_template(attr["current_count"], template)
        print(f"  {attr['attribute_type']}: {attr['attribute_value']}  "
              f"(trend_score={attr['trend_score']}, current={attr['current_count']})")
        print(f"    5-week projection: {np.round(projection, 1).tolist()}")


if __name__ == "__main__":
    run()

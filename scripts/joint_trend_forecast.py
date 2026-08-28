"""
Joint-attribute trend forecaster. Predicts next-week demand for a (category,
color, pattern) combination — not three separate signals — using a LightGBM
model trained on H&M's public transaction history and applied here to our
real Sri Lankan daily scrape data.

Methodology (matches ml/models/joint_attribute_lgbm_model.pkl exactly):
  1. One joint key per garment: "Category|Color|Pattern", not tracked separately.
  2. 4 features per key, per week: lag_1, lag_2 (last 1-2 weeks' count),
     roll_mean_4, roll_std_4 (4-week rolling mean/volatility) — all log1p-
     transformed, since raw counts range from single digits to thousands and
     an untransformed model measurably failed on that scale mismatch.
  3. Only keys with >= MIN_WEEKS of real history get a prediction — an
     attribute with 2 weeks of data doesn't get to claim a trend, same
     sample-size-awareness principle as the Laplace smoothing fix elsewhere
     in this codebase.
  4. Ranked by raw predicted_change (predicted next-week count minus current
     count), not percentage — percentage alone resurfaces the exact
     "1->2 mentions = 100% growth" noise problem already fixed once.
"""
import glob
import json
import math
import os
import pickle
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal
from app.models import Product, TrendSignal

MODEL_PATH = ROOT / "ml" / "models" / "joint_attribute_lgbm_model.pkl"
MIN_WEEKS = 6
ROLLING_WINDOW = 4

RUN_DIR_RE = __import__("re").compile(r"run_(\d{4}-\d{2}-\d{2})_")


def _load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def _parse_run_date(run_dir: str) -> datetime:
    name = os.path.basename(run_dir.rstrip("/\\"))
    m = RUN_DIR_RE.search(name)
    return datetime.strptime(m.group(1), "%Y-%m-%d")


def _load_product_joint_keys(db) -> dict:
    """product_url -> 'Category|Color|Pattern', skipping anything with an
    Unknown component — a joint key is only meaningful if all three parts
    are real."""
    rows = db.query(
        Product.product_url, Product.ml_category, Product.ml_color, Product.ml_pattern
    ).all()
    keys = {}
    for url, cat, col, pat in rows:
        if not url or not cat or not col or cat == "Unknown" or col == "Unknown":
            continue
        keys[url] = f"{cat}|{col}|{pat or 'Solid'}"
    return keys


def build_weekly_joint_counts() -> dict:
    """joint_key -> ordered list of weekly counts, oldest week first.
    Weeks are consecutive 7-day buckets starting from the earliest run."""
    db = SessionLocal()
    joint_keys = _load_product_joint_keys(db)
    db.close()

    run_folders = sorted(glob.glob(str(ROOT / "trend-data-collector" / "output" / "run_*")))
    if not run_folders:
        return {}

    first_date = _parse_run_date(run_folders[0])
    daily_counts = defaultdict(lambda: defaultdict(int))  # joint_key -> {week_idx: count}

    for run_dir in run_folders:
        run_date = _parse_run_date(run_dir)
        week_idx = (run_date - first_date).days // 7

        for file_path in glob.glob(os.path.join(run_dir, "*_garments.json")):
            if "combined" in file_path:
                continue
            try:
                garments = json.load(open(file_path, "r", encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            for g in garments:
                url = g.get("product_url")
                key = joint_keys.get(url) if url else None
                if key:
                    daily_counts[key][week_idx] += 1

    weekly_series = {}
    for key, week_map in daily_counts.items():
        max_week = max(week_map.keys())
        series = [week_map.get(w, 0) for w in range(max_week + 1)]
        weekly_series[key] = series
    return weekly_series


def compute_forecasts(weekly_series: dict, model, min_weeks: int = MIN_WEEKS) -> list:
    results = []
    for key, series in weekly_series.items():
        if len(series) < min_weeks:
            continue

        recent = series[-ROLLING_WINDOW:]
        log_recent = [math.log1p(c) for c in recent]

        lag_1 = log_recent[-1]
        lag_2 = log_recent[-2] if len(log_recent) >= 2 else log_recent[-1]
        roll_mean_4 = mean(log_recent)
        roll_std_4 = pstdev(log_recent) if len(log_recent) > 1 else 0.0

        pred_log = model.predict([[lag_1, lag_2, roll_mean_4, roll_std_4]])[0]
        predicted_next = math.expm1(max(pred_log, 0))
        current = recent[-1]
        predicted_change = predicted_next - current

        results.append({
            "joint_key": key,
            "weeks_of_history": len(series),
            "current_week_count": current,
            "predicted_next_week_count": round(predicted_next, 1),
            "predicted_change": round(predicted_change, 1),
        })

    results.sort(key=lambda r: r["predicted_change"], reverse=True)
    return results


def persist_forecasts(results: list):
    if not results:
        return
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    db.query(TrendSignal).filter(TrendSignal.attribute_type == "joint_forecast").delete()
    for r in results[:50]:
        db.add(TrendSignal(
            attribute_type="joint_forecast",
            attribute_value=r["joint_key"],
            trend_score=r["predicted_change"],
            growth_rate=round(
                (r["predicted_change"] / r["current_week_count"]) if r["current_week_count"] else 0.0, 2
            ),
            time_window="weekly_forecast",
            start_date=now,
            end_date=now,
        ))
    db.commit()
    db.close()


def run(min_weeks: int = MIN_WEEKS, persist: bool = True):
    print(f"Building weekly joint-attribute counts from real daily scrape history...")
    weekly_series = build_weekly_joint_counts()
    print(f"  {len(weekly_series)} joint attribute combinations observed.")

    eligible = sum(1 for s in weekly_series.values() if len(s) >= min_weeks)
    print(f"  {eligible} have >= {min_weeks} weeks of history (the minimum this methodology requires).")

    model = _load_model()
    results = compute_forecasts(weekly_series, model, min_weeks=min_weeks)
    print(f"\nForecasts produced: {len(results)}")
    for r in results[:10]:
        print(f"  {r['joint_key']:<45} current={r['current_week_count']:<6} "
              f"predicted_next={r['predicted_next_week_count']:<8} change={r['predicted_change']:+.1f}")

    if persist and results:
        persist_forecasts(results)
        print(f"\nPersisted top {min(50, len(results))} forecasts to TrendSignal (attribute_type='joint_forecast').")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Joint-attribute weekly trend forecaster")
    parser.add_argument("--min-weeks", type=int, default=MIN_WEEKS,
                         help=f"Minimum weeks of history required (default {MIN_WEEKS}, the methodology's real threshold)")
    parser.add_argument("--no-persist", action="store_true", help="Don't write results to the database")
    args = parser.parse_args()
    run(min_weeks=args.min_weeks, persist=not args.no_persist)

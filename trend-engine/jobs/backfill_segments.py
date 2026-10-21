"""Computes segment scores for every stored snapshot, as of that snapshot's own date (no future data).

Run once after migration 0008 so past snapshots can be graded against what happened next; the nightly
compute_trends job fills segments for new snapshots. Idempotent: safe to re-run.
Usage: python jobs/backfill_segments.py [--horizon 3|5]
"""
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.ml.engine import TrendEngine  # noqa: E402
from app.ml.segments import segment_rows  # noqa: E402
from app.models import TrendSnapshot  # noqa: E402
from app.repositories.observation_repo import ObservationRepository  # noqa: E402
from app.repositories.trend_repo import TrendRepository  # noqa: E402

MIN_DAYS_OF_HISTORY = 8


def run(horizons: tuple[int, ...] = (3, 5)) -> None:
    db = SessionLocal()
    try:
        attrs, presence = ObservationRepository(db).build_ml_panel_inputs()
        attrs["date"] = pd.to_datetime(attrs["date"])
        presence["date"] = pd.to_datetime(presence["date"])
        engine = TrendEngine()
        repo = TrendRepository(db)

        snapshots = db.scalars(
            select(TrendSnapshot).where(TrendSnapshot.horizon_days.in_(horizons)).order_by(TrendSnapshot.as_of_date)
        ).all()
        done = skipped = 0
        for snap in snapshots:
            as_of = pd.Timestamp(snap.as_of_date)
            a, p = attrs[attrs.date <= as_of], presence[presence.date <= as_of]
            if p.date.nunique() < MIN_DAYS_OF_HISTORY:
                skipped += 1
                continue
            try:
                rows = engine.rank(segment_rows(a), p, top_k=None, horizon=snap.horizon_days)
            except Exception as e:  # a very young snapshot may have too little data
                print(f"  {snap.as_of_date} h={snap.horizon_days}: skipped ({e})")
                skipped += 1
                continue
            repo.replace_segments(snap.snapshot_id, rows)
            done += 1
            print(f"  {snap.as_of_date} h={snap.horizon_days}d: {len(rows)} segments")
        print(f"done: {done} snapshots filled, {skipped} skipped (too little history)")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backfill segment scores for stored snapshots")
    parser.add_argument("--horizon", type=int, default=None, help="3 or 5; omit for both")
    args = parser.parse_args()
    run(horizons=(args.horizon,) if args.horizon else (3, 5))

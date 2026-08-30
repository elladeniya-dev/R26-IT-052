"""
Runs the trend engine once and persists a snapshot. Called by GitHub Actions
after jobs/ingest.py in the daily pipeline (architecture spec §5). Scoring
never runs inside an API request — the API only ever reads what this job
writes.

    python jobs/compute_trends.py               # both horizons (3, 5)
    python jobs/compute_trends.py --horizon 3    # just one
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.services.trend_service import HORIZONS, TrendService  # noqa: E402


def run(horizons: tuple[int, ...] = HORIZONS) -> None:
    db = SessionLocal()
    try:
        service = TrendService(db)
        print(f"model: {service.engine.model_name}  ic: {service.engine.model_ic}")
        for horizon in horizons:
            try:
                result = service.compute_snapshot(horizon_days=horizon)
                print(f"horizon={horizon}d  snapshot_id={result['snapshot_id']}  scored={result['n_scored']}")
            except Exception as e:
                print(f"horizon={horizon}d  FAILED: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compute and persist a trend snapshot")
    parser.add_argument("--horizon", type=int, default=None, help="3 or 5; omit to run both")
    args = parser.parse_args()
    run(horizons=(args.horizon,) if args.horizon else HORIZONS)

"""
Computes weekly TrendSignal rows from TrendObservation data and persists them.
Standalone equivalent of the GET /trends/analyze endpoint, for use without
running the API server (e.g. right after generate_trend_observations.py).
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models import TrendObservation, TrendSignal
from app.services.trend_analysis_service import calculate_trend_signals


def compute_and_persist():
    db = SessionLocal()

    observations = db.query(TrendObservation).all()
    if not observations:
        print("No trend observations found. Run generate_trend_observations.py first.")
        db.close()
        return

    latest_date = max(obs.collected_at for obs in observations)
    current_start = latest_date - timedelta(days=7)
    current_end = latest_date
    previous_start = current_start - timedelta(days=7)
    previous_end = current_start

    analyzed_results, meta = calculate_trend_signals(
        observations, current_start, current_end, previous_start, previous_end
    )

    if not analyzed_results:
        print("No observations found in current or previous analysis windows.")
        db.close()
        return

    db.query(TrendSignal).filter(
        TrendSignal.time_window == "weekly",
        TrendSignal.start_date == current_start,
        TrendSignal.end_date == current_end,
    ).delete(synchronize_session=False)

    for item in analyzed_results:
        db.add(TrendSignal(
            attribute_type=item["attribute_type"],
            attribute_value=item["attribute_value"],
            trend_score=item["trend_score"],
            growth_rate=item["growth_rate"],
            time_window=item["time_window"],
            start_date=item["start_date"],
            end_date=item["end_date"],
        ))

    db.commit()
    db.close()

    print(f"Persisted {len(analyzed_results)} trend signals for window {current_start} -> {current_end}")
    print("\nTop 10 by trend_score:")
    for item in analyzed_results[:10]:
        print(f"  {item['attribute_type']:>20} | {item['attribute_value']:<20} score={item['trend_score']} growth={item['growth_rate']}")


if __name__ == "__main__":
    compute_and_persist()

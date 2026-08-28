"""
Backtests our own trend_score methodology against real outcomes, using data
we already have — no waiting required. Picks a cutoff partway through the
24 real days of history, computes trend_score using ONLY data up to that
cutoff (exactly like the live system would have at that point in time),
then checks what REALLY happened in the days after the cutoff (which we
already know, since it's in the past). If "rising"-flagged attributes
really did see higher real growth afterward than "weak"-flagged ones,
that's genuine predictive validity — not just a formula that looks
reasonable on paper.
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models import TrendObservation
from app.services.trend_analysis_service import calculate_trend_signals


def backtest(cutoff_days_from_start: int = 15, holdout_days: int = 7):
    db = SessionLocal()
    all_obs = db.query(TrendObservation).order_by(TrendObservation.collected_at).all()
    db.close()

    if not all_obs:
        print("No observations found.")
        return

    earliest = min(o.collected_at for o in all_obs)
    latest = max(o.collected_at for o in all_obs)
    total_days = (latest - earliest).days
    print(f"Real history available: {earliest.date()} -> {latest.date()} ({total_days} days)")

    cutoff = earliest + timedelta(days=cutoff_days_from_start)
    holdout_end = cutoff + timedelta(days=holdout_days)
    if holdout_end > latest:
        print(f"Not enough data after the cutoff for a {holdout_days}-day holdout "
              f"(cutoff={cutoff.date()}, latest={latest.date()}). Reducing holdout.")
        holdout_end = latest

    print(f"Backtest cutoff: {cutoff.date()}  (using only data before this date to predict)")
    print(f"Holdout window:  {cutoff.date()} -> {holdout_end.date()}  (checking real outcomes here)")

    # --- Step 1: compute trend_score using ONLY data before the cutoff ---
    train_obs = [o for o in all_obs if o.collected_at < cutoff]
    current_start = cutoff - timedelta(days=7)
    current_end = cutoff
    previous_start = current_start - timedelta(days=7)
    previous_end = current_start

    signals, _ = calculate_trend_signals(train_obs, current_start, current_end, previous_start, previous_end)
    if not signals:
        print("No signals computed at this cutoff — try an earlier/later cutoff_days_from_start.")
        return

    predicted_rising = {(s["attribute_type"], s["attribute_value"]) for s in signals if s["trend_score"] >= 0.55}
    predicted_weak = {(s["attribute_type"], s["attribute_value"]) for s in signals if s["trend_score"] < 0.35}
    print(f"\nAt cutoff: {len(predicted_rising)} attributes flagged 'rising', {len(predicted_weak)} flagged 'weak'")

    # --- Step 2: what ACTUALLY happened after the cutoff (real, already known) ---
    # calculate_trend_signals lowercases attribute_type/attribute_value
    # internally (see key = (obs.attribute_type.lower(), obs.attribute_value.lower())
    # in trend_analysis_service.py) — match that here or every key silently
    # fails to line up between predicted_rising/predicted_weak and these counts.
    holdout_obs = [o for o in all_obs if cutoff <= o.collected_at <= holdout_end]
    actual_counts = {}
    for o in holdout_obs:
        key = (o.attribute_type.lower(), o.attribute_value.lower())
        actual_counts[key] = actual_counts.get(key, 0) + o.mention_count

    # Also get their PRE-cutoff counts for a fair comparison (growth, not just volume)
    pre_counts = {}
    for o in train_obs:
        if o.collected_at >= current_start:
            key = (o.attribute_type.lower(), o.attribute_value.lower())
            pre_counts[key] = pre_counts.get(key, 0) + o.mention_count

    def avg_forward_growth(keys):
        growths = []
        for k in keys:
            before = pre_counts.get(k, 0)
            after = actual_counts.get(k, 0)
            if before > 0:
                growths.append((after - before) / before)
            elif after > 0:
                growths.append(1.0)
        return growths

    rising_growth = avg_forward_growth(predicted_rising)
    weak_growth = avg_forward_growth(predicted_weak)

    print("\n=== Real outcome check (not retrospective — these are genuinely future relative to the cutoff) ===")
    if rising_growth:
        print(f"Attributes flagged RISING at cutoff: avg real forward growth = {sum(rising_growth)/len(rising_growth):+.2%}  (n={len(rising_growth)})")
    else:
        print("No 'rising' attributes had measurable pre-cutoff volume to compare.")
    if weak_growth:
        print(f"Attributes flagged WEAK at cutoff:   avg real forward growth = {sum(weak_growth)/len(weak_growth):+.2%}  (n={len(weak_growth)})")
    else:
        print("No 'weak' attributes had measurable pre-cutoff volume to compare.")

    if rising_growth and weak_growth:
        diff = (sum(rising_growth)/len(rising_growth)) - (sum(weak_growth)/len(weak_growth))
        print(f"\nDifference (rising - weak): {diff:+.2%}")
        if diff > 0:
            print("Rising-flagged attributes DID show higher real subsequent growth than weak-flagged ones.")
        else:
            print("No real predictive edge found at this cutoff — rising-flagged attributes did NOT outperform weak-flagged ones.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cutoff-day", type=int, default=15)
    parser.add_argument("--holdout-days", type=int, default=7)
    args = parser.parse_args()
    backtest(cutoff_days_from_start=args.cutoff_day, holdout_days=args.holdout_days)

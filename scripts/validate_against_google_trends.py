"""
Independent, external validation of our currently-flagged "rising" attributes
against real Google Trends search interest — a completely different data
source from our own (confounded, still-young) scrape history. If attributes
we flag as rising also show real rising search interest, that's genuine
outside evidence, available today, not something that needs weeks to accrue.

Uses trendspyg (actively maintained; pytrends was archived April 2025 with
no official replacement) — free, local, no API key.
"""
import sys
import time
from pathlib import Path
from statistics import mean

import trendspyg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.pipeline.trend_shape_template import get_rising_sl_attributes, RISING_THRESHOLD

GEO = "LK"  # Sri Lanka. Falls back to a broader region if a term has too
            # little local search volume to return a meaningful signal.
FALLBACK_GEO = ""  # worldwide
TIMEFRAME = "today 3-m"


def fetch_recent_vs_prior(keyword: str, geo: str) -> dict:
    """Splits the available window in half: recent vs. prior, mirroring our
    own current-window-vs-previous-window trend_score logic — same shape of
    comparison, entirely different, independent data source."""
    try:
        data = trendspyg.download_google_trends_interest_over_time(
            keyword, geo=geo, timeframe=TIMEFRAME, output_format="dict",
            max_retries=3, retry_wait=5.0,
        )
    except trendspyg.TrendspygException as err:
        return {"available": False, "error": str(err).splitlines()[0]}

    if not data:
        return {"available": False}

    values = [row["value"] for row in data]
    midpoint = len(values) // 2
    prior = values[:midpoint]
    recent = values[midpoint:]

    if not prior or not recent:
        return {"available": False}

    prior_avg = mean(prior)
    recent_avg = mean(recent)
    total_signal = sum(values)

    return {
        "available": True,
        "prior_avg": round(prior_avg, 1),
        "recent_avg": round(recent_avg, 1),
        "change_pct": round(((recent_avg - prior_avg) / prior_avg) * 100, 1) if prior_avg > 0 else None,
        "total_signal": total_signal,  # near-zero across the whole window = too little search volume to trust
    }


def run(top_n: int = 8):
    db = SessionLocal()
    rising = get_rising_sl_attributes(db, threshold=RISING_THRESHOLD)
    db.close()

    if not rising:
        print(f"No attributes currently flagged rising (trend_score >= {RISING_THRESHOLD}). Nothing to validate.")
        return

    # Dedupe attribute_value across new_arrival_* / plain variants — same
    # underlying keyword either way.
    seen = set()
    candidates = []
    for r in rising:
        val = r["attribute_value"].lower()
        if val not in seen:
            seen.add(val)
            candidates.append(r)

    print(f"Checking {min(top_n, len(candidates))} of {len(candidates)} attributes our system flags as rising, "
          f"against real Google Trends search interest ({GEO or 'worldwide'}, last 3 months)...\n")

    agree, disagree, no_signal = 0, 0, 0

    for i, r in enumerate(candidates[:top_n]):
        if i > 0:
            time.sleep(20)  # real, necessary spacing — Google throttled a burst of 5 rapid queries earlier
        keyword = r["attribute_value"]
        result = fetch_recent_vs_prior(keyword, GEO)

        if not result["available"] or result["total_signal"] < 20:
            # Too little real search volume in Sri Lanka specifically to
            # mean anything — try the worldwide signal instead, clearly
            # labeled as such, rather than reporting a near-all-zero series
            # as if it were meaningful.
            time.sleep(10)
            result = fetch_recent_vs_prior(keyword, FALLBACK_GEO)
            geo_used = "worldwide (SL volume too low)"
        else:
            geo_used = GEO

        if not result["available"]:
            reason = result.get("error", "search volume too low to validate against, even worldwide")
            print(f"  {keyword:<20} [{r['attribute_type']}] our_score={r['trend_score']}  -> NO_SIGNAL ({reason})")
            no_signal += 1
            continue
        if result["total_signal"] < 20:
            print(f"  {keyword:<20} [{r['attribute_type']}] our_score={r['trend_score']}  "
                  f"-> NO_SIGNAL (real search volume too low to validate against, even worldwide)")
            no_signal += 1
            continue

        trend_direction = "RISING" if (result["change_pct"] or 0) > 5 else (
            "FALLING" if (result["change_pct"] or 0) < -5 else "FLAT"
        )
        agreement = "AGREES" if trend_direction == "RISING" else "disagrees"
        if trend_direction == "RISING":
            agree += 1
        else:
            disagree += 1

        print(f"  {keyword:<20} [{r['attribute_type']}] our_score={r['trend_score']}  "
              f"google_trends({geo_used})={trend_direction} ({result['change_pct']:+.1f}% recent vs prior)  -> {agreement}")

    print(f"\n=== Summary ===")
    print(f"Real search interest AGREES our system's 'rising' flag: {agree}")
    print(f"Real search interest DISAGREES: {disagree}")
    print(f"No usable external signal (too low search volume): {no_signal}")


if __name__ == "__main__":
    run()

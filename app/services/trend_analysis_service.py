from typing import List, Dict, Any, Tuple
from datetime import datetime


def calculate_trend_signals(
    observations: list,
    current_start: datetime,
    current_end: datetime,
    previous_start: datetime,
    previous_end: datetime,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    current_counts = {}
    previous_counts = {}
    current_ranks = {}

    for obs in observations:
        key = (obs.attribute_type.lower(), obs.attribute_value.lower())

        if current_start <= obs.collected_at <= current_end:
            current_counts[key] = current_counts.get(key, 0) + obs.mention_count

            if obs.rank_position is not None:
                if key not in current_ranks:
                    current_ranks[key] = []
                current_ranks[key].append(obs.rank_position)

        elif previous_start <= obs.collected_at < previous_end:
            previous_counts[key] = previous_counts.get(key, 0) + obs.mention_count

    all_keys = set(current_counts.keys()) | set(previous_counts.keys())

    if not all_keys:
        return [], {}

    max_current_count = max(current_counts.values()) if current_counts else 1
    analyzed_results = []

    for key in all_keys:
        attribute_type, attribute_value = key

        current_count = current_counts.get(key, 0)
        previous_count = previous_counts.get(key, 0)

        if previous_count == 0:
            growth_rate = 1.0 if current_count > 0 else 0.0
        else:
            growth_rate = (current_count - previous_count) / previous_count

        growth_score = max(min(growth_rate, 1.0), 0.0)

        count_score = current_count / max_current_count if max_current_count > 0 else 0.0
        count_score = max(min(count_score, 1.0), 0.0)

        ranks = current_ranks.get(key, [])

        if ranks:
            average_rank = sum(ranks) / len(ranks)
            rank_score = 1 - ((average_rank - 1) / 20)
            rank_score = max(min(rank_score, 1.0), 0.0)
        else:
            average_rank = None
            rank_score = 0.5

        trend_score = round(
            (0.50 * growth_score) + (0.30 * count_score) + (0.20 * rank_score),
            2,
        )

        growth_rate = round(growth_rate, 2)

        analyzed_results.append(
            {
                "attribute_type": attribute_type,
                "attribute_value": attribute_value,
                "current_count": current_count,
                "previous_count": previous_count,
                "growth_rate": growth_rate,
                "growth_score": round(growth_score, 2),
                "count_score": round(count_score, 2),
                "rank_score": round(rank_score, 2),
                "average_rank": average_rank,
                "trend_score": trend_score,
                "time_window": "weekly",
                "start_date": current_start,
                "end_date": current_end,
            }
        )

    analyzed_results.sort(
        key=lambda item: item["trend_score"],
        reverse=True,
    )

    meta = {
        "formula": "trend_score = 0.50 * growth_score + 0.30 * count_score + 0.20 * rank_score",
        "current_period": {
            "start_date": current_start,
            "end_date": current_end,
        },
        "previous_period": {
            "start_date": previous_start,
            "end_date": previous_end,
        },
    }
    return analyzed_results, meta


def derive_prediction_features_from_signal(signal, index: int) -> dict:
    trend_score = float(signal.trend_score or 0)
    growth_rate = float(signal.growth_rate or 0)

    purchase_count = max(1, int(trend_score * 1000))

    if growth_rate > -0.95:
        previous_purchase_count = max(
            1,
            int(purchase_count / (1 + growth_rate)),
        )
    else:
        previous_purchase_count = purchase_count

    mention_growth = purchase_count - previous_purchase_count

    weekly_rank = index
    previous_rank = index + 2 if growth_rate > 0 else index
    rank_change = weekly_rank - previous_rank

    count_score = min(1.0, trend_score)
    growth_score = min(1.0, max(0.0, growth_rate))
    rank_score = 1 / weekly_rank

    return {
        "attribute_type": signal.attribute_type,
        "attribute_value": signal.attribute_value,
        "purchase_count": purchase_count,
        "previous_purchase_count": previous_purchase_count,
        "mention_growth": mention_growth,
        "growth_rate": growth_rate,
        "weekly_rank": weekly_rank,
        "previous_rank": previous_rank,
        "rank_change": rank_change,
        "count_score": count_score,
        "growth_score": growth_score,
        "rank_score": rank_score,
        "trend_score": trend_score,
    }

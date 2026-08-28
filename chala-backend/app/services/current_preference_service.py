from collections import defaultdict


# ============================================================
# CURRENT PREFERENCE HELPERS
# ============================================================

def get_onboarding_weight(
    interaction_count: int,
) -> float:
    """
    Gradually reduces onboarding influence
    as more interactions are collected.

    < 5 interactions  -> 1.00
    < 10              -> 0.75
    < 20              -> 0.50
    20+               -> 0.25
    """

    if interaction_count < 5:
        return 1.0

    if interaction_count < 10:
        return 0.75

    if interaction_count < 20:
        return 0.50

    return 0.25


def normalize_current_preference_scores(
    scores: dict,
    top_n: int = 3,
    minimum_score: float = 0.30,
) -> dict:
    """
    Current Preference normalization.

    1. Remove non-positive values
    2. Normalize strongest value to 1.0
    3. Remove values below 0.30
    4. Sort strongest -> weakest
    5. Return Top 3
    """

    if not scores:
        return {}

    positive_scores = {
        key: value
        for key, value in scores.items()
        if value > 0
    }

    if not positive_scores:
        return {}

    max_score = max(
        positive_scores.values()
    )

    normalized_scores = {
        key: round(
            value / max_score,
            2,
        )
        for key, value
        in positive_scores.items()
    }

    filtered_scores = {
        key: value
        for key, value
        in normalized_scores.items()
        if value >= minimum_score
    }

    sorted_scores = sorted(
        filtered_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return dict(
        sorted_scores[:top_n]
    )


def combine_current_preferences(
    onboarding_values,
    learned_weights,
    onboarding_weight: float,
) -> dict:
    """
    Current preference =
        onboarding influence
        +
        learned interaction behavior
    """

    combined_scores = defaultdict(
        float
    )

    if onboarding_values:

        for value in onboarding_values:

            if value:
                combined_scores[
                    value
                ] += onboarding_weight

    if learned_weights:

        for key, value in (
            learned_weights.items()
        ):

            if (
                key
                and value is not None
            ):

                combined_scores[
                    key
                ] += float(value)

    return normalize_current_preference_scores(
        dict(combined_scores)
    )
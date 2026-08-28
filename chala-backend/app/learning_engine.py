from collections import defaultdict
from datetime import datetime, timezone


# Interaction influence becomes half after 30 days
RECENCY_HALF_LIFE_DAYS = 30.0


def normalize_weights(weight_dict: dict) -> dict:
    """
    Normalizes positive scores to values between 0 and 1.
    """

    if not weight_dict:
        return {}

    positive_weights = {
        key: value
        for key, value in weight_dict.items()
        if value > 0
    }

    if not positive_weights:
        return {}

    max_value = max(positive_weights.values())

    normalized = {
        key: round(value / max_value, 2)
        for key, value in positive_weights.items()
    }

    # Sort from strongest to weakest preference
    return dict(
        sorted(
            normalized.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )


def add_weight(
    weight_dict: dict,
    key,
    value: float,
):
    """
    Adds a score to a product attribute.
    Supports single values and lists.
    """

    if key is None:
        return

    if isinstance(key, list):
        for item in key:
            if item:
                weight_dict[item] += value
    else:
        if key:
            weight_dict[key] += value


def calculate_recency_factor(created_at) -> float:
    """
    Reduces the influence of older interactions.
    """

    if created_at is None:
        return 1.0

    interaction_time = created_at

    # Make sure the timestamp uses UTC
    if interaction_time.tzinfo is None:
        interaction_time = interaction_time.replace(
            tzinfo=timezone.utc
        )

    current_time = datetime.now(timezone.utc)

    age = current_time - interaction_time

    age_in_days = max(
        age.total_seconds() / 86400.0,
        0.0,
    )

    # 30-day half-life time decay
    recency_factor = 0.5 ** (
        age_in_days / RECENCY_HALF_LIFE_DAYS
    )

    return recency_factor


def calculate_learned_preferences(
    interactions: list,
    products_by_id: dict,
) -> dict:
    """
    Learns category, color, style, brand and occasion
    preferences from interaction strength
    and interaction recency.
    """

    category_scores = defaultdict(float)
    color_scores = defaultdict(float)
    style_scores = defaultdict(float)
    brand_scores = defaultdict(float)

    # NEW:
    # Stores dynamically learned occasion scores.
    occasion_scores = defaultdict(float)

    for interaction in interactions:
        product = products_by_id.get(
            interaction.item_id
        )

        if not product:
            continue

        interaction_value = (
            interaction.interaction_value
        )

        if interaction_value is None:
            continue

        # Recent interactions have more influence
        recency_factor = calculate_recency_factor(
            interaction.created_at
        )

        effective_value = (
            float(interaction_value)
            * recency_factor
        )

        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        add_weight(
            category_scores,
            product.category,
            effective_value,
        )

        # ----------------------------------------------------
        # COLOR
        # ----------------------------------------------------

        add_weight(
            color_scores,
            product.color,
            effective_value,
        )

        # ----------------------------------------------------
        # STYLE
        # ----------------------------------------------------

        add_weight(
            style_scores,
            product.style,
            effective_value,
        )

        # ----------------------------------------------------
        # BRAND
        # ----------------------------------------------------

        add_weight(
            brand_scores,
            product.brand,
            effective_value,
        )

        # ----------------------------------------------------
        # OCCASION
        # ----------------------------------------------------

        add_weight(
            occasion_scores,
            product.occasions,
            effective_value,
        )

    return {
        "category_weights": normalize_weights(
            category_scores
        ),

        "color_weights": normalize_weights(
            color_scores
        ),

        "style_weights": normalize_weights(
            style_scores
        ),

        "brand_weights": normalize_weights(
            brand_scores
        ),

        # NEW
        "occasion_weights": normalize_weights(
            occasion_scores
        ),
    }


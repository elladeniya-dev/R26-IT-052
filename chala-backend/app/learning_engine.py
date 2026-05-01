from collections import defaultdict


def normalize_weights(weight_dict: dict) -> dict:
    """
    Converts raw scores into values between 0 and 1.
    Example:
    Raw: {"Tops": 8, "Dresses": 4}
    Normalized: {"Tops": 1.0, "Dresses": 0.5}
    """

    if not weight_dict:
        return {}

    # Remove zero/negative values from final positive preference result
    positive_weights = {
        key: value for key, value in weight_dict.items()
        if value > 0
    }

    if not positive_weights:
        return {}

    max_value = max(positive_weights.values())

    return {
        key: round(value / max_value, 2)
        for key, value in positive_weights.items()
    }


def add_weight(weight_dict: dict, key, value: float):
    """
    Safely adds weight to a dictionary.
    Handles empty/null values.
    """

    if key is None:
        return

    if isinstance(key, list):
        for item in key:
            if item:
                weight_dict[item] += value
    else:
        weight_dict[key] += value


def calculate_learned_preferences(interactions: list, products_by_id: dict) -> dict:
    """
    Calculates learned user preferences using:
    - user interactions
    - product category, color, and style

    Each interaction has an interaction_value:
    view = 1
    click = 2
    save = 3
    select = 4
    dislike = -2
    """

    category_scores = defaultdict(float)
    color_scores = defaultdict(float)
    style_scores = defaultdict(float)
    brand_scores = defaultdict(float)

    for interaction in interactions:
        product = products_by_id.get(interaction.item_id)

        if not product:
            continue

        value = interaction.interaction_value

        add_weight(category_scores, product.category, value)
        add_weight(color_scores, product.color, value)
        add_weight(style_scores, product.style, value)
        add_weight(brand_scores, product.brand, value)

    return {
        "category_weights": normalize_weights(category_scores),
        "color_weights": normalize_weights(color_scores),
        "style_weights": normalize_weights(style_scores),
        "brand_weights": normalize_weights(brand_scores)
    }
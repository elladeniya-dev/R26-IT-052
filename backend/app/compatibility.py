from typing import List, Dict, Tuple


COLOR_COMPATIBILITY_MAP = {
    "black": ["white", "beige", "grey", "gray", "blue", "denim blue", "red"],
    "white": ["black", "blue", "beige", "brown", "red", "grey", "gray"],
    "beige": ["white", "brown", "black", "blue", "red"],
    "blue": ["white", "black", "grey", "gray", "beige"],
    "denim blue": ["white", "black", "grey", "gray", "beige"],
    "red": ["black", "white", "beige"],
    "brown": ["white", "beige", "black"],
    "grey": ["black", "white", "blue", "beige"],
    "gray": ["black", "white", "blue", "beige"],
}


OCCASION_STYLE_MAP = {
    "casual": ["casual", "streetwear", "everyday"],
    "office": ["formal", "office", "smart casual"],
    "formal": ["formal", "office", "elegant"],
    "party": ["party", "elegant", "trendy"],
    "sports": ["sports", "activewear"],
}


VALID_CATEGORY_STRUCTURES = [
    {"top", "bottom"},
    {"top", "bottom", "outerwear"},
    {"dress"},
    {"dress", "outerwear"},
]


def normalize_text_list(values) -> List[str]:
    """
    Converts list values into lowercase clean text.
    Example:
    ["Casual", "Office"] -> ["casual", "office"]
    """
    if not values:
        return []

    if isinstance(values, str):
        return [values.strip().lower()]

    return [str(value).strip().lower() for value in values]


def calculate_style_match_score(outfit_items: List[Dict]) -> Tuple[float, List[str]]:
    """
    Checks whether outfit items have matching styles.
    If many items share the same style, score becomes higher.
    """
    reason_tags = []
    all_styles = []

    for item in outfit_items:
        item_styles = normalize_text_list(item.get("style"))
        all_styles.extend(item_styles)

    if not all_styles:
        return 0.0, ["missing style information"]

    unique_styles = set(all_styles)

    if len(unique_styles) == 1:
        style_name = list(unique_styles)[0]
        reason_tags.append(f"matching {style_name} style")
        return 1.0, reason_tags

    # Count most common style
    style_counts = {}
    for style in all_styles:
        style_counts[style] = style_counts.get(style, 0) + 1

    max_count = max(style_counts.values())
    score = max_count / len(outfit_items)

    if score >= 0.7:
        reason_tags.append("most items have similar style")
    elif score >= 0.4:
        reason_tags.append("some items share similar style")
    else:
        reason_tags.append("styles are less similar")

    return round(score, 2), reason_tags


def calculate_color_match_score(outfit_items: List[Dict]) -> Tuple[float, List[str]]:
    """
    Checks whether colors in the outfit are compatible.
    Uses simple color compatibility map.
    """
    reason_tags = []
    item_colors = []

    for item in outfit_items:
        colors = normalize_text_list(item.get("color"))
        if colors:
            item_colors.append(colors[0])

    if len(item_colors) <= 1:
        return 1.0, ["single color item, no color conflict"]

    total_pairs = 0
    matching_pairs = 0

    for i in range(len(item_colors)):
        for j in range(i + 1, len(item_colors)):
            color_a = item_colors[i]
            color_b = item_colors[j]
            total_pairs += 1

            if color_a == color_b:
                matching_pairs += 1
            elif color_b in COLOR_COMPATIBILITY_MAP.get(color_a, []):
                matching_pairs += 1
            elif color_a in COLOR_COMPATIBILITY_MAP.get(color_b, []):
                matching_pairs += 1

    if total_pairs == 0:
        return 0.0, ["not enough colors to compare"]

    score = matching_pairs / total_pairs

    if score >= 0.8:
        reason_tags.append("suitable color combination")
    elif score >= 0.5:
        reason_tags.append("acceptable color combination")
    else:
        reason_tags.append("weak color combination")

    return round(score, 2), reason_tags


def calculate_category_match_score(outfit_items: List[Dict]) -> Tuple[float, List[str]]:
    """
    Checks whether the selected items form a valid outfit structure.
    Example:
    top + bottom
    top + bottom + outerwear
    dress + outerwear
    """
    reason_tags = []

    categories = {item.get("category", "").lower() for item in outfit_items}

    if categories in VALID_CATEGORY_STRUCTURES:
        reason_tags.append("categories form a complete outfit")
        return 1.0, reason_tags

    if "top" in categories and "bottom" in categories:
        reason_tags.append("top and bottom combination found")
        return 0.9, reason_tags

    if "dress" in categories:
        reason_tags.append("dress-based outfit found")
        return 0.8, reason_tags

    reason_tags.append("outfit category structure is incomplete")
    return 0.4, reason_tags


def calculate_occasion_match_score(
    outfit_items: List[Dict],
    occasion: str
) -> Tuple[float, List[str]]:
    """
    Checks whether item styles match the requested occasion.
    Example:
    occasion casual -> prefer casual products
    occasion office -> prefer formal/office/smart casual products
    """
    reason_tags = []

    if not occasion:
        return 0.5, ["no occasion provided"]

    occasion = occasion.strip().lower()
    preferred_styles = OCCASION_STYLE_MAP.get(occasion, [])

    if not preferred_styles:
        return 0.5, ["unknown occasion, neutral occasion score"]

    matched_items = 0

    for item in outfit_items:
        item_styles = normalize_text_list(item.get("style"))

        for style in item_styles:
            if style in preferred_styles:
                matched_items += 1
                break

    score = matched_items / len(outfit_items)

    if score >= 0.8:
        reason_tags.append(f"highly suitable for {occasion}")
    elif score >= 0.5:
        reason_tags.append(f"partially suitable for {occasion}")
    else:
        reason_tags.append(f"less suitable for {occasion}")

    return round(score, 2), reason_tags


def calculate_compatibility_score(
    outfit_items: List[Dict],
    occasion: str
) -> Dict:
    """
    Final compatibility score calculation.
    """
    style_score, style_reasons = calculate_style_match_score(outfit_items)
    color_score, color_reasons = calculate_color_match_score(outfit_items)
    category_score, category_reasons = calculate_category_match_score(outfit_items)
    occasion_score, occasion_reasons = calculate_occasion_match_score(
        outfit_items,
        occasion
    )

    final_score = (
        0.40 * style_score +
        0.30 * color_score +
        0.20 * category_score +
        0.10 * occasion_score
    )

    reason_tags = (
        style_reasons +
        color_reasons +
        category_reasons +
        occasion_reasons
    )

    return {
        "compatibility_score": round(final_score, 2),
        "reason_tags": reason_tags,
        "score_breakdown": {
            "style_match_score": style_score,
            "color_match_score": color_score,
            "category_match_score": category_score,
            "occasion_match_score": occasion_score
        }
    }
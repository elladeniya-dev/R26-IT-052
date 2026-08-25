from collections import Counter
from typing import List, Dict, Tuple


COLOR_COMPATIBILITY_MAP = {
    "black": ["white", "beige", "cream", "grey", "gray", "blue", "navy", "denim blue", "red"],
    "white": ["black", "blue", "navy", "beige", "cream", "brown", "red", "grey", "gray", "green"],
    "beige": ["white", "cream", "brown", "black", "blue", "navy", "red", "olive"],
    "cream": ["white", "beige", "brown", "black", "blue", "navy", "olive"],
    "blue": ["white", "black", "grey", "gray", "beige", "cream", "brown"],
    "navy": ["white", "beige", "cream", "grey", "gray", "brown", "red"],
    "denim blue": ["white", "black", "grey", "gray", "beige", "cream"],
    "red": ["black", "white", "beige", "cream", "navy"],
    "brown": ["white", "beige", "cream", "black", "blue", "olive"],
    "grey": ["black", "white", "blue", "navy", "beige", "red"],
    "gray": ["black", "white", "blue", "navy", "beige", "red"],
    "green": ["white", "black", "beige", "cream", "brown"],
    "olive": ["white", "beige", "cream", "black", "brown"],
}


NEUTRAL_COLORS = {
    "black",
    "white",
    "beige",
    "cream",
    "grey",
    "gray",
    "navy",
    "brown",
    "denim blue",
}


OCCASION_STYLE_MAP = {
    "casual": ["casual", "streetwear", "everyday", "smart casual"],
    "office": ["formal", "office", "smart casual", "elegant"],
    "formal": ["formal", "office", "elegant", "smart casual"],
    "party": ["party", "elegant", "trendy", "formal"],
    "sports": ["sports", "activewear", "casual"],
}


STYLE_COMPATIBILITY_MAP = {
    "casual": ["streetwear", "everyday", "smart casual", "sports"],
    "streetwear": ["casual", "everyday", "trendy", "sports"],
    "everyday": ["casual", "streetwear", "smart casual"],
    "smart casual": ["casual", "office", "formal", "elegant", "everyday"],
    "office": ["formal", "smart casual", "elegant"],
    "formal": ["office", "smart casual", "elegant", "party"],
    "elegant": ["formal", "office", "party", "smart casual"],
    "party": ["elegant", "trendy", "formal"],
    "trendy": ["party", "streetwear", "casual"],
    "sports": ["activewear", "casual", "streetwear"],
    "activewear": ["sports", "casual"],
}


VALID_CATEGORY_STRUCTURES = [
    {"top", "bottom"},
    {"top", "bottom", "outerwear"},
    {"top", "bottom", "footwear"},
    {"top", "bottom", "accessory"},
    {"top", "bottom", "outerwear", "footwear"},
    {"top", "bottom", "outerwear", "accessory"},
    {"top", "bottom", "footwear", "accessory"},
    {"top", "bottom", "outerwear", "footwear", "accessory"},
    {"dress"},
    {"dress", "outerwear"},
    {"dress", "footwear"},
    {"dress", "accessory"},
    {"dress", "outerwear", "footwear"},
    {"dress", "outerwear", "accessory"},
    {"dress", "footwear", "accessory"},
    {"dress", "outerwear", "footwear", "accessory"},
]


CORE_CATEGORIES = {"top", "bottom", "dress", "outerwear"}


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

    return [
        str(value).strip().lower()
        for value in values
        if str(value).strip()
    ]


def are_styles_compatible(style_a: str, style_b: str) -> bool:
    if style_a == style_b:
        return True

    return (
        style_b in STYLE_COMPATIBILITY_MAP.get(style_a, [])
        or style_a in STYLE_COMPATIBILITY_MAP.get(style_b, [])
    )


def item_styles_are_compatible(styles_a: List[str], styles_b: List[str]) -> bool:
    for style_a in styles_a:
        for style_b in styles_b:
            if are_styles_compatible(style_a, style_b):
                return True

    return False


def are_colors_compatible(color_a: str, color_b: str) -> bool:
    if color_a == color_b:
        return True

    if color_b in COLOR_COMPATIBILITY_MAP.get(color_a, []):
        return True

    if color_a in COLOR_COMPATIBILITY_MAP.get(color_b, []):
        return True

    # Neutral colors generally work as balancing pieces.
    return color_a in NEUTRAL_COLORS and color_b in NEUTRAL_COLORS


def calculate_style_match_score(outfit_items: List[Dict]) -> Tuple[float, List[str]]:
    """
    Checks whether outfit items have matching or compatible styles.
    """
    reason_tags = []
    item_style_groups = []

    for item in outfit_items:
        item_styles = normalize_text_list(item.get("style"))
        if item_styles:
            item_style_groups.append(item_styles)

    if not item_style_groups:
        return 0.0, ["missing style information"]

    all_styles = [
        style
        for style_group in item_style_groups
        for style in style_group
    ]

    unique_styles = set(all_styles)

    if len(unique_styles) == 1:
        style_name = list(unique_styles)[0]
        reason_tags.append(f"matching {style_name} style")
        return 1.0, reason_tags

    if len(item_style_groups) == 1:
        reason_tags.append("single styled item, no style conflict")
        return 0.8, reason_tags

    total_pairs = 0
    compatible_pairs = 0

    for i in range(len(item_style_groups)):
        for j in range(i + 1, len(item_style_groups)):
            total_pairs += 1

            if item_styles_are_compatible(item_style_groups[i], item_style_groups[j]):
                compatible_pairs += 1

    if total_pairs == 0:
        return 0.0, ["not enough style information to compare"]

    style_counts = Counter(all_styles)
    dominant_style, dominant_count = style_counts.most_common(1)[0]
    pair_score = compatible_pairs / total_pairs
    coverage_score = dominant_count / len(item_style_groups)
    score = (0.75 * pair_score) + (0.25 * min(coverage_score, 1.0))

    if score >= 0.7:
        reason_tags.append(f"items follow compatible {dominant_style} styling")
    elif score >= 0.4:
        reason_tags.append("some items share compatible style")
    else:
        reason_tags.append("style conflict detected")

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

            if are_colors_compatible(color_a, color_b):
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

    category_list = [
        item.get("category", "").strip().lower()
        for item in outfit_items
        if item.get("category")
    ]
    categories = set(category_list)

    if not categories:
        return 0.0, ["missing category information"]

    category_counts = Counter(category_list)
    duplicate_core_categories = [
        category
        for category, count in category_counts.items()
        if count > 1 and category in CORE_CATEGORIES
    ]

    if "dress" in categories and ({"top", "bottom"} & categories):
        reason_tags.append("dress should not be mixed with separate top or bottom items")
        return 0.3, reason_tags

    if duplicate_core_categories:
        reason_tags.append("duplicate main clothing category found")
        return 0.5, reason_tags

    if categories in VALID_CATEGORY_STRUCTURES:
        reason_tags.append("categories form a complete outfit")
        return 1.0, reason_tags

    if "top" in categories and "bottom" in categories:
        reason_tags.append("top and bottom combination found")
        return 0.9, reason_tags

    if "dress" in categories:
        reason_tags.append("dress-based outfit found")
        return 0.8, reason_tags

    if categories.intersection({"footwear", "accessory"}) and len(categories) == 1:
        reason_tags.append("supporting item needs main clothing pieces")
        return 0.3, reason_tags

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

    if not outfit_items:
        return 0.0, ["no outfit items to evaluate"]

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

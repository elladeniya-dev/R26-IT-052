ALLOWED_INSIGHT_ATTRIBUTE_TYPES = [
    "category",
    "color",
    "pattern",
    "style",
    "material",
]

EXCLUDED_INSIGHT_KEYWORDS = [
    "bra",
    "bralette",
    "panty",
    "panties",
    "underwear",
    "lingerie",
    "brief",
    "briefs",
    "thong",
    "bikini bottom",
    "nightwear",
    "sleepwear",
    "sleeve",
    "half sleeve",
    "balloon sleeve",
    "short sleeve",
    "long sleeve",
    "sleeveless",
    "fitted",
    "regular fit",
    "oversized",
    "baggy",
    "cropped",
    "straight leg",
    "wide leg",
    "mid waist",
    "high waist",
    "relaxed",
    "loose",
    "flare",
    "non-denim",
    "other",
    "unknown",
    "bodysuit",
    "bustier",
]


def is_safe_user_facing_trend(attribute_type: str, attribute_value: str) -> bool:
    trend_type = attribute_type.lower().strip()
    value = attribute_value.lower().strip()

    if trend_type not in ALLOWED_INSIGHT_ATTRIBUTE_TYPES:
        return False

    for blocked_keyword in EXCLUDED_INSIGHT_KEYWORDS:
        if blocked_keyword in value:
            return False

    return True

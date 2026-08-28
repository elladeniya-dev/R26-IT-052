import os
import re
from functools import lru_cache

from sentence_transformers import SentenceTransformer, util


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml_models",
    "koji-fashion-sim-v1",
)


CATEGORY_ALIASES = {
    "tops": "top",
    "top": "top",
    "shirts": "top",
    "shirt": "top",
    "blouses": "top",
    "blouse": "top",
    "tees": "top",
    "tee": "top",
    "t-shirt": "top",
    "crop top": "top",
    "dresses": "dress",
    "dress": "dress",
    "pants": "pants",
    "pant": "pants",
    "trousers": "pants",
    "trouser": "pants",
    "jeans": "jeans",
    "jean": "jeans",
    "shorts": "shorts",
    "short": "shorts",
    "skirts": "skirt",
    "skirt": "skirt",
    "jumpsuits": "jumpsuit",
    "jumpsuit": "jumpsuit",
    "leggings": "leggings",
    "legging": "leggings",
    "blazers": "blazer",
    "blazer": "blazer",
}


COLOR_ALIASES = {
    "black": {"black", "jet black"},
    "white": {"white", "off white", "sheer white", "ivory"},
    "red": {"red", "maroon", "burgundy", "wine", "cherry red"},
    "blue": {"blue", "navy", "navy blue", "dark blue", "light blue", "sky blue", "denim"},
    "green": {"green", "olive", "olive green", "sage", "mint", "dark green"},
    "pink": {"pink", "baby pink", "serene pink", "rose", "vintage rose", "blush"},
    "beige": {"beige", "cream", "nude", "sand", "khaki", "natural"},
    "grey": {"grey", "gray", "charcoal", "charcoal grey", "stone grey", "silver"},
    "brown": {"brown", "dark brown", "mocha", "coffee", "chocolate"},
    "yellow": {"yellow", "butter yellow", "mustard"},
    "purple": {"purple", "lilac", "lavender"},
    "orange": {"orange", "rust", "terracotta"},
    "multi": {"multi", "printed", "print", "floral", "striped", "pattern"},
}


STYLE_ALIASES = {
    "formal": {
        "formal",
        "office",
        "office wear",
        "work",
        "workwear",
        "work wear",
        "smart_casual",
        "smart casual",
        "blazer",
        "tailored",
    },
    "casual": {
        "casual",
        "daily",
        "daily wear",
        "everyday",
        "lifestyle",
        "relaxed",
        "athleisure",
    },
    "party": {
        "party",
        "party wear",
        "evening",
        "evening wear",
        "cocktail",
        "occasion",
        "special events",
    },
    "trendy": {
        "trendy",
        "trend",
        "new_in",
        "new in",
        "new arrival",
        "oversized",
        "fitted",
        "denim",
    },
    "elegant": {
        "elegant",
        "formal",
        "evening",
        "party",
        "smart_casual",
        "smart casual",
        "classic",
    },
    "minimal": {
        "minimal",
        "minimalist",
        "basic",
        "classic",
        "clean",
        "plain",
        "solid",
        "simple",
    },
    "activewear": {
        "activewear",
        "active wear",
        "gym",
        "training",
        "workout",
        "athleisure",
        "sport",
    },
    "summer": {
        "summer",
        "linen",
        "cotton",
        "sleeveless",
        "natural_blends",
        "natural blends",
    },
    "floral": {
        "floral",
        "flower",
        "printed",
        "print",
        "pattern",
    },
    "denim": {
        "denim",
        "jeans",
        "jean",
    },
}


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Loads the locally saved sentence-transformer model only once.
    After first load, it reuses the same model while backend is running.
    """
    return SentenceTransformer(MODEL_PATH)


def _clean_text(value):
    if value is None:
        return ""

    value = str(value).strip().lower()
    value = value.replace("-", " ").replace("_", " ")
    value = re.sub(r"\s+", " ", value)

    return value


def _to_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, set):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()

    if not text:
        return []

    return [text]


def _normalize_category(value):
    text = _clean_text(value)

    for alias, canonical in CATEGORY_ALIASES.items():
        if alias in text:
            return canonical

    return text


def _normalize_color(value):
    text = _clean_text(value)

    for canonical, aliases in COLOR_ALIASES.items():
        for alias in aliases:
            if alias in text:
                return canonical

    return text


def _expand_style_tokens(values):
    raw_values = _to_list(values)
    combined_text = " ".join(_clean_text(value) for value in raw_values)
    expanded_tokens = set()

    for value in raw_values:
        cleaned_value = _clean_text(value)
        if cleaned_value:
            expanded_tokens.add(cleaned_value)

    for canonical_style, aliases in STYLE_ALIASES.items():
        for alias in aliases:
            if alias in combined_text:
                expanded_tokens.add(canonical_style)

    return expanded_tokens


def _get_requested_categories(request):
    return {
        _normalize_category(category)
        for category in _to_list(getattr(request, "preferred_categories", []))
        if _normalize_category(category)
    }


def _get_product_categories(product):
    values = [
        getattr(product, "category", ""),
        getattr(product, "subcategory", ""),
        getattr(product, "title", ""),
    ]

    return {
        _normalize_category(value)
        for value in values
        if _normalize_category(value)
    }


def _get_requested_colors(request):
    return {
        _normalize_color(color)
        for color in _to_list(getattr(request, "preferred_colors", []))
        if _normalize_color(color)
    }


def _get_product_colors(product):
    return {
        _normalize_color(color)
        for color in _to_list(getattr(product, "color", []))
        if _normalize_color(color)
    }


def _get_requested_brands(request):
    brands = {
        _clean_text(brand)
        for brand in _to_list(getattr(request, "preferred_brands", []))
        if _clean_text(brand)
    }

    ignored_values = {
        "no specific brand",
        "any brand",
        "none",
        "no brand",
        "all",
    }

    return {brand for brand in brands if brand not in ignored_values}


def _get_product_brand(product):
    return _clean_text(getattr(product, "brand", ""))


def _get_requested_styles(request):
    return _expand_style_tokens(getattr(request, "preferred_styles", []))


def _get_product_styles(product):
    style_values = _to_list(getattr(product, "style", []))

    extra_values = [
        getattr(product, "title", ""),
        getattr(product, "category", ""),
        getattr(product, "subcategory", ""),
        getattr(product, "description", ""),
    ]

    return _expand_style_tokens(style_values + extra_values)


def _has_style_conflict(requested_styles, product_styles):
    """
    Prevents clearly opposite style cases from getting high ML scores.

    Example:
    requested = formal / office
    product = party / evening / casual dress
    product has no formal/workwear/smart_casual signal
    """

    formal_requested = bool(
        requested_styles.intersection({"formal", "workwear", "smart_casual"})
    )
    party_requested = bool(
        requested_styles.intersection({"party", "evening"})
    )
    minimal_requested = bool(
        requested_styles.intersection({"minimal"})
    )
    active_requested = bool(
        requested_styles.intersection({"activewear"})
    )

    product_formal = bool(
        product_styles.intersection({"formal", "workwear", "smart_casual"})
    )
    product_party = bool(
        product_styles.intersection({"party", "evening"})
    )
    product_minimal = bool(
        product_styles.intersection({"minimal", "basic", "classic", "clean", "solid"})
    )
    product_active = bool(
        product_styles.intersection({"activewear", "athleisure"})
    )
    product_floral_or_loud = bool(
        product_styles.intersection({"floral", "printed", "party", "evening"})
    )

    if formal_requested and product_party and not product_formal:
        return True

    if party_requested and product_formal and not product_party:
        return True

    if minimal_requested and product_floral_or_loud and not product_minimal:
        return True

    if active_requested and product_formal and not product_active:
        return True

    return False


def _attribute_analysis(product, request):
    requested_categories = _get_requested_categories(request)
    product_categories = _get_product_categories(product)

    requested_colors = _get_requested_colors(request)
    product_colors = _get_product_colors(product)

    requested_styles = _get_requested_styles(request)
    product_styles = _get_product_styles(product)

    requested_brands = _get_requested_brands(request)
    product_brand = _get_product_brand(product)

    category_match = (
        True if not requested_categories
        else bool(requested_categories.intersection(product_categories))
    )

    color_match = (
        True if not requested_colors
        else bool(requested_colors.intersection(product_colors))
    )

    style_match = (
        True if not requested_styles
        else bool(requested_styles.intersection(product_styles))
    )

    brand_match = (
        True if not requested_brands
        else product_brand in requested_brands
    )

    style_conflict = _has_style_conflict(requested_styles, product_styles)

    return {
        "category_match": category_match,
        "color_match": color_match,
        "style_match": style_match,
        "brand_match": brand_match,
        "style_conflict": style_conflict,
        "requested_styles": requested_styles,
        "product_styles": product_styles,
    }


def build_user_preference_text(request):
    categories = ", ".join(_to_list(getattr(request, "preferred_categories", [])))
    colors = ", ".join(_to_list(getattr(request, "preferred_colors", [])))
    styles = ", ".join(_to_list(getattr(request, "preferred_styles", [])))
    brands = ", ".join(_to_list(getattr(request, "preferred_brands", [])))

    return (
        "User fashion preference profile. "
        f"Preferred clothing categories: {categories}. "
        f"Preferred colors: {colors}. "
        f"Preferred fashion styles: {styles}. "
        f"Preferred brands: {brands}. "
        "The selected style preferences are important matching constraints. "
        "Products with conflicting fashion styles should be considered less relevant."
    )


def build_product_text(product):
    colors = ", ".join(_to_list(getattr(product, "color", [])))
    styles = ", ".join(_to_list(getattr(product, "style", [])))

    description = getattr(product, "description", "") or ""
    description = str(description)

    # Avoid very long descriptions dominating the embedding.
    if len(description) > 500:
        description = description[:500]

    return (
        "Fashion product profile. "
        f"Product title: {getattr(product, 'title', '')}. "
        f"Category: {getattr(product, 'category', '')}. "
        f"Subcategory: {getattr(product, 'subcategory', '')}. "
        f"Colors: {colors}. "
        f"Styles: {styles}. "
        f"Brand: {getattr(product, 'brand', '')}. "
        f"Description: {description}."
    )


def _calibrate_cosine_similarity(raw_similarity):
    """
    Converts cosine similarity into a stricter 0-1 score.

    Old method:
    (similarity + 1) / 2

    Problem:
    It made many average products look very high.

    New method:
    Treat weak/medium similarities more strictly.
    """

    min_useful_similarity = 0.25
    strong_similarity = 0.85

    calibrated = (
        (raw_similarity - min_useful_similarity)
        / (strong_similarity - min_useful_similarity)
    )

    return max(0.0, min(1.0, calibrated))


def _apply_guardrails(base_score, product, request):
    analysis = _attribute_analysis(product, request)

    score = base_score

    if analysis["category_match"]:
        score += 0.04
    else:
        score -= 0.18
        score = min(score, 0.62)

    if analysis["color_match"]:
        score += 0.03
    else:
        score -= 0.06

    if analysis["style_match"]:
        score += 0.08
    else:
        score -= 0.20
        score = min(score, 0.72)

    if analysis["brand_match"]:
        score += 0.03
    else:
        score -= 0.08

    if analysis["style_conflict"]:
        score -= 0.35
        score = min(score, 0.48)

    # Do not allow normal products to display as 100% ML similarity too easily.
    if (
        analysis["category_match"]
        and analysis["color_match"]
        and analysis["style_match"]
        and analysis["brand_match"]
        and not analysis["style_conflict"]
    ):
        score = min(score, 0.96)
    else:
        score = min(score, 0.90)

    return max(0.0, min(1.0, score))


def calculate_ml_similarity_score(product, request):
    """
    Calculates a stricter ML-based similarity score between user preferences
    and product details.

    This combines:
    - Fine-tuned sentence-transformer semantic similarity
    - Category/color/style/brand guardrails
    - Style conflict penalty

    Returns:
    - float value between 0 and 1
    """

    model = get_embedding_model()

    user_text = build_user_preference_text(request)
    product_text = build_product_text(product)

    user_embedding = model.encode(user_text, convert_to_tensor=True)
    product_embedding = model.encode(product_text, convert_to_tensor=True)

    raw_similarity = util.cos_sim(user_embedding, product_embedding).item()
    calibrated_similarity = _calibrate_cosine_similarity(raw_similarity)

    final_score = _apply_guardrails(
        base_score=calibrated_similarity,
        product=product,
        request=request,
    )

    return round(final_score, 4)
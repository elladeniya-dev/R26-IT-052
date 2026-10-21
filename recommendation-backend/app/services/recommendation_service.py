import math
import re
from collections import defaultdict

from app.models.product import Product
from app.services.ml_similarity_service import calculate_ml_similarity_score
from app.services.fashion_attribute_normalizer import (
    canonicalize_attribute,
    tokenize_attribute_values,
)
from app.services.product_quality_service import is_non_fashion_product
from app.services.preference_weighting_service import (
    get_explicit_categories,
    matched_preference_confidence,
    normalize_text_list,
    prioritize_explicit_category_candidates,
)


PLACEHOLDER_IMAGE_URLS = {
    "https://example.com/carnage-placeholder.jpg",
    "https://example.com/gflock-placeholder.jpg",
    "https://example.com/kelly-felder-placeholder.jpg",
}

EXCLUDED_SOURCES = {"sample_data", "sample_crawler","chenara_dodge",}
FAKE_URL_DOMAIN = "example.com"


def matches_price_range(price, price_min, price_max):
    if price_min is None and price_max is None:
        return None

    if price is None:
        return False

    if price_min is not None and price < price_min:
        return False

    if price_max is not None and price > price_max:
        return False

    return True


def is_real_recommendable_product(product: Product):
    source = (product.source or "").lower()
    product_url = (product.product_url or "").lower()
    image_url = (product.image_url or "").lower()

    if product.availability is not True:
        return False

    if is_non_fashion_product(product):
        return False

    if source in EXCLUDED_SOURCES:
        return False

    if FAKE_URL_DOMAIN in product_url:
        return False

    if FAKE_URL_DOMAIN in image_url:
        return False

    return True


def calculate_user_match_score(product: Product, request):
    score = 0.0
    total_weight = 0.0
    reason_tags = []

    preferred_categories = normalize_text_list(request.preferred_categories, "category")
    preferred_colors = normalize_text_list(request.preferred_colors, "color")
    preferred_styles = normalize_text_list(request.preferred_styles, "style")
    preferred_brands = normalize_text_list(request.preferred_brands, "brand")

    if preferred_categories:
        total_weight += 0.30
        match_confidence = matched_preference_confidence(
            product.category,
            preferred_categories,
            getattr(request, "category_weights", {}),
            "category",
        )
        if match_confidence is not None:
            score += 0.30 * match_confidence
            reason_tags.append("matches your preferred category")

    if preferred_colors:
        total_weight += 0.20
        match_confidence = matched_preference_confidence(
            product.color,
            preferred_colors,
            getattr(request, "color_weights", {}),
            "color",
        )
        if match_confidence is not None:
            score += 0.20 * match_confidence
            reason_tags.append("matches your preferred color")

    if preferred_styles:
        total_weight += 0.25
        match_confidence = matched_preference_confidence(
            product.style,
            preferred_styles,
            getattr(request, "style_weights", {}),
            "style",
        )
        if match_confidence is not None:
            score += 0.25 * match_confidence
            reason_tags.append("matches your preferred style")

    # Brand is a soft preference only.
    # Matching brands get a boost, but non-matching brands are still allowed
    # if category, color, style, or ML semantic similarity are strong.
    if preferred_brands:
        total_weight += 0.15
        match_confidence = matched_preference_confidence(
            product.brand,
            preferred_brands,
            getattr(request, "brand_weights", {}),
            "brand",
        )
        if match_confidence is not None:
            score += 0.15 * match_confidence
            reason_tags.append("from your preferred brand")

    price_match = matches_price_range(
        product.price,
        request.price_min,
        request.price_max,
    )

    if price_match is not None:
        total_weight += 0.10
        if price_match:
            score += 0.10
            reason_tags.append("within your price range")

    if total_weight == 0:
        return 0.0, reason_tags

    return round(score / total_weight, 4), reason_tags


def has_real_image_url(image_url):
    if not image_url:
        return False

    return image_url not in PLACEHOLDER_IMAGE_URLS


def calculate_product_quality_score(product: Product):
    quality_checks = [
        bool(has_real_image_url(product.image_url)),
        bool(product.product_url),
        bool(product.description),
        product.price is not None,
        product.availability is True,
    ]

    passed_checks = sum(1 for check in quality_checks if check)
    return round(passed_checks / len(quality_checks), 4)


def build_quality_reason_tags(product: Product, product_quality_score):
    reason_tags = []

    if product.availability is True:
        reason_tags.append("available now")

    has_complete_details = (
        has_real_image_url(product.image_url)
        and bool(product.product_url)
        and bool(product.description)
        and product.price is not None
    )

    if has_complete_details:
        reason_tags.append("has complete product details")
    elif product_quality_score >= 0.8:
        reason_tags.append("has strong product details")

    return reason_tags


def build_ml_reason_tags(ml_similarity_score):
    reason_tags = []

    if ml_similarity_score >= 0.75:
        reason_tags.append("semantically similar to your style preferences")
    elif ml_similarity_score >= 0.60:
        reason_tags.append("partially similar to your style preferences")

    return reason_tags


def calculate_recommendation_score(product: Product, request):
    user_match_score, reason_tags = calculate_user_match_score(product, request)
    product_quality_score = calculate_product_quality_score(product)
    ml_similarity_score = calculate_ml_similarity_score(product, request)

    final_score = (
        (0.60 * user_match_score)
        + (0.25 * ml_similarity_score)
        + (0.15 * product_quality_score)
    )

    reason_tags.extend(build_ml_reason_tags(ml_similarity_score))
    reason_tags.extend(build_quality_reason_tags(product, product_quality_score))

    return (
        round(final_score, 4),
        round(user_match_score, 4),
        round(ml_similarity_score, 4),
        round(product_quality_score, 4),
        reason_tags,
    )


def normalize_group_key(value):
    if not value:
        return "unknown"

    return str(value).strip().lower()


def build_product_family_key(item):
    """
    Prevents many color/variant rows from the same product dominating the list.

    Example:
    - 90's Bootcut Jeans mid wash
    - 90's Bootcut Jeans dark wash

    These are still allowed, but limited so the user sees more variety.
    """

    source = normalize_group_key(item.get("source"))
    title = normalize_group_key(item.get("title"))

    cleaned_title = re.sub(r"[^a-z0-9]+", "_", title).strip("_")

    return f"{source}_{cleaned_title}"


def diversify_recommendations(scored_products, max_results):
    """
    Re-ranks recommendations to keep the list realistic and diverse.

    Main idea:
    - Keep high scoring products first.
    - Do not allow one brand/source to dominate the whole result list.
    - Do not allow too many variants of the same product title.
    - If not enough diverse products exist, fill remaining slots using the
      next best scored products.
    """

    if not scored_products:
        return []

    max_results = max_results or 5

    # Example:
    # max_results = 10 -> max 4 products from same source/brand
    # max_results = 15 -> max 6 products from same source/brand
    max_per_source = max(2, math.ceil(max_results * 0.40))

    # Allows a maximum of 2 variants from same product title.
    # Example: same jeans in dark wash and mid wash.
    max_per_product_family = 2

    selected = []
    selected_item_ids = set()

    source_counts = defaultdict(int)
    product_family_counts = defaultdict(int)

    # First pass: strict diversity.
    for item in scored_products:
        if len(selected) >= max_results:
            break

        item_id = item.get("item_id")
        source_key = normalize_group_key(item.get("source") or item.get("brand"))
        product_family_key = build_product_family_key(item)

        if item_id in selected_item_ids:
            continue

        if source_counts[source_key] >= max_per_source:
            continue

        if product_family_counts[product_family_key] >= max_per_product_family:
            continue

        selected.append(item)
        selected_item_ids.add(item_id)
        source_counts[source_key] += 1
        product_family_counts[product_family_key] += 1

    # Second pass: if there are not enough diverse products,
    # fill the remaining slots using the next best scored products.
    # This prevents returning only 4 products when the DB has limited matches.
    for item in scored_products:
        if len(selected) >= max_results:
            break

        item_id = item.get("item_id")

        if item_id in selected_item_ids:
            continue

        selected.append(item)
        selected_item_ids.add(item_id)

    return selected[:max_results]


def generate_recommendations(db, request):
    """
    Generates recommendations only from currently available products.

    This prevents old, hidden, sample, placeholder, and out-of-stock
    products from being recommended to the user.

    Final output is score-ranked first, then diversity re-ranked so that
    preferred brands get a boost without dominating the whole list.
    """

    products = (
        db.query(Product)
        .filter(Product.availability.is_(True))
        .all()
    )

    scored_products = []
    requested_style = canonicalize_attribute(
        getattr(request, "style_filter", None), "style"
    )
    apply_style_filter = bool(requested_style and requested_style != "all")

    for product in products:
        if not is_real_recommendable_product(product):
            continue

        product_styles = tokenize_attribute_values(product.style, "style")
        if apply_style_filter and requested_style not in product_styles:
            continue

        (
            final_score,
            user_match_score,
            ml_similarity_score,
            product_quality_score,
            reason_tags,
        ) = calculate_recommendation_score(product, request)

        # Allow products if they have either explicit preference match
        # or strong semantic ML similarity.
        if user_match_score > 0 or ml_similarity_score >= 0.60:
            scored_products.append(
                {
                    "item_id": product.item_id,
                    "title": product.title,
                    "category": canonicalize_attribute(product.category, "category"),
                    "color": tokenize_attribute_values(product.color, "color"),
                    "style": product_styles,
                    "brand": product.brand,
                    "source": product.source,
                    "price": product.price,
                    "image_url": product.image_url,
                    "product_url": product.product_url,
                    "final_score": final_score,
                    "user_match_score": user_match_score,
                    "ml_similarity_score": ml_similarity_score,
                    "product_quality_score": product_quality_score,
                    "reason_tags": reason_tags,
                }
            )

    scored_products.sort(
        key=lambda item: item["final_score"],
        reverse=True,
    )

    explicit_categories = get_explicit_categories(
        getattr(request, "preference_sources", {})
    )
    safeguarded_products = prioritize_explicit_category_candidates(
        scored_products=scored_products,
        explicit_categories=explicit_categories,
        max_results=request.max_results or 5,
    )

    return diversify_recommendations(
        scored_products=safeguarded_products,
        max_results=request.max_results,
    )

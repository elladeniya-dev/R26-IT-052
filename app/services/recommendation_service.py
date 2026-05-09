from app.models.product import Product


PLACEHOLDER_IMAGE_URLS = {
    "https://example.com/carnage-placeholder.jpg",
    "https://example.com/gflock-placeholder.jpg"
}
EXCLUDED_SOURCES = {"sample_data", "sample_crawler"}
FAKE_URL_DOMAIN = "example.com"


def normalize_text_list(values):
    return [value.lower() for value in values or []]


def has_overlap(product_values, preferred_values):
    product_values = normalize_text_list(product_values)
    preferred_values = normalize_text_list(preferred_values)

    return any(value in preferred_values for value in product_values)


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

    preferred_categories = normalize_text_list(request.preferred_categories)
    preferred_colors = normalize_text_list(request.preferred_colors)
    preferred_styles = normalize_text_list(request.preferred_styles)
    preferred_brands = normalize_text_list(request.preferred_brands)

    if preferred_categories:
        total_weight += 0.30
        if product.category and product.category.lower() in preferred_categories:
            score += 0.30
            reason_tags.append("matches your preferred category")

    if preferred_colors:
        total_weight += 0.20
        if has_overlap(product.color, preferred_colors):
            score += 0.20
            reason_tags.append("matches your preferred color")

    if preferred_styles:
        total_weight += 0.25
        if has_overlap(product.style, preferred_styles):
            score += 0.25
            reason_tags.append("matches your preferred style")

    if preferred_brands:
        total_weight += 0.15
        if product.brand and product.brand.lower() in preferred_brands:
            score += 0.15
            reason_tags.append("from your preferred brand")

    price_match = matches_price_range(
        product.price,
        request.price_min,
        request.price_max
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
        product.availability is True
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


def calculate_recommendation_score(product: Product, request):
    user_match_score, reason_tags = calculate_user_match_score(product, request)
    product_quality_score = calculate_product_quality_score(product)

    final_score = (0.85 * user_match_score) + (0.15 * product_quality_score)
    reason_tags.extend(build_quality_reason_tags(product, product_quality_score))

    return (
        round(final_score, 4),
        round(user_match_score, 4),
        round(product_quality_score, 4),
        reason_tags
    )


def generate_recommendations(db, request):
    products = db.query(Product).filter(Product.availability == True).all()

    scored_products = []

    for product in products:
        if not is_real_recommendable_product(product):
            continue

        (
            final_score,
            user_match_score,
            product_quality_score,
            reason_tags
        ) = calculate_recommendation_score(product, request)

        if user_match_score > 0:
            scored_products.append({
                "item_id": product.item_id,
                "title": product.title,
                "category": product.category,
                "color": product.color,
                "style": product.style,
                "brand": product.brand,
                "source": product.source,
                "price": product.price,
                "image_url": product.image_url,
                "product_url": product.product_url,
                "final_score": final_score,
                "user_match_score": user_match_score,
                "product_quality_score": product_quality_score,
                "reason_tags": reason_tags
            })

    scored_products.sort(key=lambda item: item["final_score"], reverse=True)

    return scored_products[:request.max_results]

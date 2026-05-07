from app.models.product import Product


def calculate_match_score(product: Product, preferred_categories, preferred_colors, preferred_styles):
    score = 0.0
    reason_tags = []

    # Category match: 40%
    if product.category in preferred_categories:
        score += 0.4
        reason_tags.append("matches preferred category")

    # Color match: 30%
    product_colors = product.color or []
    if any(color in preferred_colors for color in product_colors):
        score += 0.3
        reason_tags.append("matches preferred color")

    # Style match: 30%
    product_styles = product.style or []
    if any(style in preferred_styles for style in product_styles):
        score += 0.3
        reason_tags.append("matches preferred style")

    return round(score, 2), reason_tags


def generate_recommendations(db, request):
    products = db.query(Product).filter(Product.availability == True).all()

    scored_products = []

    for product in products:
        final_score, reason_tags = calculate_match_score(
            product=product,
            preferred_categories=request.preferred_categories,
            preferred_colors=request.preferred_colors,
            preferred_styles=request.preferred_styles
        )

        if final_score > 0:
            scored_products.append({
                "item_id": product.item_id,
                "title": product.title,
                "category": product.category,
                "color": product.color,
                "style": product.style,
                "price": product.price,
                "image_url": product.image_url,
                "product_url": product.product_url,
                "final_score": final_score,
                "reason_tags": reason_tags
            })

    scored_products.sort(key=lambda item: item["final_score"], reverse=True)

    return scored_products[:request.max_results]
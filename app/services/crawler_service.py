from app.models.product import Product


def save_crawled_products(db, products):
    inserted_count = 0
    skipped_count = 0

    for product_data in products:
        existing_product = db.query(Product).filter(
            Product.item_id == product_data["item_id"]
        ).first()

        if existing_product:
            skipped_count += 1
            continue

        product = Product(**product_data)
        db.add(product)
        inserted_count += 1

    db.commit()

    return inserted_count, skipped_count


def generate_sample_crawled_products(request):
    """
    Temporary crawler simulation.

    Later, this function will be replaced with real web crawling logic.
    For now, it creates sample products based on the crawl request.
    """

    category = request.category or "top"
    color = request.colors[0] if request.colors else "black"
    style = request.styles[0] if request.styles else "casual"

    return [
        {
            "item_id": f"CRAWL_{category}_{color}_{style}_001",
            "title": f"{color.title()} {style.title()} {category.title()}",
            "category": category,
            "subcategory": None,
            "color": [color],
            "style": [style],
            "brand": "Sample Crawled Brand",
            "price": 4500,
            "currency": "LKR",
            "image_url": "https://example.com/crawled-product.jpg",
            "product_url": "https://example.com/crawled-product",
            "source": "sample_crawler",
            "description": f"Sample crawled {style} {category} in {color}",
            "availability": True
        }
    ]
from app.models.product import Product
from app.services.crawlers.carnage_crawler import crawl_carnage_crop_tops
from app.services.crawlers.gflock_crawler import crawl_gflock_dresses


def save_crawled_products(db, products):
    inserted_count = 0
    skipped_count = 0
    updated_count = 0

    for product_data in products:
        existing_product = db.query(Product).filter(
            Product.item_id == product_data["item_id"]
        ).first()

        if existing_product:
            existing_product.title = product_data["title"]
            existing_product.category = product_data["category"]
            existing_product.subcategory = product_data["subcategory"]
            existing_product.color = product_data["color"]
            existing_product.style = product_data["style"]
            existing_product.brand = product_data["brand"]
            existing_product.price = product_data["price"]
            existing_product.currency = product_data["currency"]
            existing_product.image_url = product_data["image_url"]
            existing_product.product_url = product_data["product_url"]
            existing_product.source = product_data["source"]
            existing_product.description = product_data["description"]
            existing_product.availability = product_data["availability"]

            updated_count += 1
            continue

        product = Product(**product_data)
        db.add(product)
        inserted_count += 1

    db.commit()

    return inserted_count, skipped_count, updated_count


def generate_sample_crawled_products(request):
    """
    Main crawler coordinator.

    Keeps the existing route contract while choosing the correct brand/category
    crawler for the request.
    """

    category = (request.category or "top").lower()
    max_items = request.max_items or 10

    if category == "dress":
        return crawl_gflock_dresses(max_items=max_items)

    return crawl_carnage_crop_tops(max_items=max_items)

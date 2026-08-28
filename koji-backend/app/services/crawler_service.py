from app.models.product import Product
from app.services.crawlers.carnage_crawler import crawl_carnage_crop_tops
from app.services.crawlers.gflock_crawler import crawl_gflock_dresses
from app.services.crawlers.kelly_felder_crawler import crawl_kelly_felder_dresses
from app.services.crawlers.zigzag_crawler import crawl_zigzag_products
from app.services.crawlers.chenara_dodge_crawler import crawl_chenara_dodge_products
from app.services.crawlers.bellini_crawler import crawl_bellini_products

def save_crawled_products(db, products):
    inserted_count = 0
    skipped_count = 0
    updated_count = 0

    for product_data in products:
        existing_product = (
            db.query(Product)
            .filter(Product.item_id == product_data["item_id"])
            .first()
        )

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


def _safe_run_crawler(crawler_name, crawler_function, max_items):
    """
    Runs one crawler safely.

    If one store is down, the whole crawler endpoint should not crash.
    Example:
    - Gflock fails with 503
    - Kelly Felder still runs and saves products
    """

    try:
        products = crawler_function(max_items=max_items)
        print(f"{crawler_name} crawler success: {len(products)} products")
        return products

    except Exception as error:
        print(f"{crawler_name} crawler failed: {error}")
        return []


def generate_sample_crawled_products(request):
    """
    Main crawler coordinator.

    Supported category values:
    - category = "all"          -> Gflock + Carnage + Kelly Felder + Zigzag
    - category = "gflock"       -> Gflock only
    - category = "carnage"      -> Carnage only
    - category = "kelly_felder" -> Kelly Felder only
    - category = "zigzag"       -> Zigzag only

    If one crawler fails, the remaining crawlers still continue.
    """

    category = (request.category or "all").lower()
    max_items = request.max_items or 10

    if category == "all":
        gflock_products = _safe_run_crawler(
            crawler_name="Gflock",
            crawler_function=crawl_gflock_dresses,
            max_items=max_items,
        )

        bellini_products = _safe_run_crawler(
            crawler_name="Bellini",
            crawler_function=crawl_bellini_products,
            max_items=max_items,
        )

        carnage_products = _safe_run_crawler(
            crawler_name="Carnage",
            crawler_function=crawl_carnage_crop_tops,
            max_items=max_items,
        )

        kelly_felder_products = _safe_run_crawler(
            crawler_name="Kelly Felder",
            crawler_function=crawl_kelly_felder_dresses,
            max_items=max_items,
        )

        zigzag_products = _safe_run_crawler(
            crawler_name="Zigzag",
            crawler_function=crawl_zigzag_products,
            max_items=max_items,
        )

        chenara_dodge_products = _safe_run_crawler(
            crawler_name="Chenara Dodge",
            crawler_function=crawl_chenara_dodge_products,
            max_items=max_items,
        )

        return (
            gflock_products
            + carnage_products
            + kelly_felder_products
            + zigzag_products
            + chenara_dodge_products
            + bellini_products

        )

    if category == "gflock":
        return _safe_run_crawler(
            crawler_name="Gflock",
            crawler_function=crawl_gflock_dresses,
            max_items=max_items,
        )

    if category == "carnage":
        return _safe_run_crawler(
            crawler_name="Carnage",
            crawler_function=crawl_carnage_crop_tops,
            max_items=max_items,
        )

    if category == "bellini":
        return _safe_run_crawler(
        crawler_name="Bellini",
        crawler_function=crawl_bellini_products,
        max_items=max_items,
        )

    if category == "kelly_felder":
        return _safe_run_crawler(
            crawler_name="Kelly Felder",
            crawler_function=crawl_kelly_felder_dresses,
            max_items=max_items,
        )

    if category == "zigzag":
        return _safe_run_crawler(
            crawler_name="Zigzag",
            crawler_function=crawl_zigzag_products,
            max_items=max_items,
        )

    if category == "chenara_dodge" or category == "chenara":
        return _safe_run_crawler(
        crawler_name="Chenara Dodge",
        crawler_function=crawl_chenara_dodge_products,
        max_items=max_items,
    )
    

    return []
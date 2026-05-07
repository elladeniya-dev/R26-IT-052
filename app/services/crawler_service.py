import re
import requests
from bs4 import BeautifulSoup

from app.models.product import Product


CARNAGE_CROP_TOPS_URL = "https://incarnage.com/collections/womens-crop-tops"


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


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def remove_emojis(text):
    return re.sub(
        r"[^\w\s.,/&'()-]",
        "",
        text
    ).strip()


def infer_color_from_title(title):
    title_lower = title.lower()

    color_keywords = {
        "black": ["black", "jet black"],
        "white": ["white", "off white"],
        "brown": ["brown", "mocha"],
        "grey": ["grey", "gray", "slate grey"],
        "green": ["green", "olive"],
        "blue": ["blue", "navy"],
        "red": ["red"],
        "pink": ["pink"],
        "beige": ["beige", "cream"],
        "purple": ["purple"],
        "yellow": ["yellow"]
    }

    matched_colors = []

    for color, keywords in color_keywords.items():
        for keyword in keywords:
            if keyword in title_lower:
                matched_colors.append(color)
                break

    return matched_colors if matched_colors else ["unknown"]


def create_item_id(product_url):
    slug = product_url.rstrip("/").split("/")[-1]
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", slug).strip("_").lower()
    return f"CARNAGE_{slug}"


def extract_price(text):
    price_match = re.search(r"LKR\s*([\d,]+(?:\.\d{2})?)", text)

    if not price_match:
        return None

    price_text = price_match.group(1).replace(",", "")

    try:
        return float(price_text)
    except ValueError:
        return None


def extract_title(text):
    text = clean_text(text)

    # Remove common badge/status words
    text = re.sub(
        r"\b(new|popular|style|best seller|sold out)\b",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove discount words like "58% off"
    text = re.sub(r"\d+%\s*off", "", text, flags=re.IGNORECASE)

    # Remove price and everything after first price
    text = re.split(r"LKR\s*[\d,]+(?:\.\d{2})?", text)[0]

    return remove_emojis(clean_text(text))

def extract_product_detail_data(product_url):
    """
    Opens a Carnage product detail page and extracts more accurate product data.
    This improves collection-page crawling by getting exact color and description.
    """

    try:
        response = requests.get(
            product_url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = clean_text(soup.get_text(" ", strip=True))

        # Extract exact color from text like "Color: Mocha Brown"
        color_match = re.search(
            r"Color:\s*([A-Za-z\s]+?)(?:\s+Select size|\s+S\s+M\s+L|\s+Add to cart)",
            page_text,
            flags=re.IGNORECASE
        )

        extracted_color_text = None
        if color_match:
            extracted_color_text = clean_text(color_match.group(1))

        # Extract useful description from Product details section
        description = None
        description_match = re.search(
            r"Product details\s+(.*?)(?:Key Features|Material Composition|Care Details|Free standard shipping|Size guide)",
            page_text,
            flags=re.IGNORECASE
        )

        if description_match:
            description = clean_text(description_match.group(1))

        # Check availability
        is_sold_out = "sold out" in page_text.lower()

        return {
            "color_text": extracted_color_text,
            "description": description,
            "availability": not is_sold_out
        }

    except Exception:
        return {
            "color_text": None,
            "description": None,
            "availability": True
        }

def crawl_carnage_crop_tops(max_items=10):
    response = requests.get(
        CARNAGE_CROP_TOPS_URL,
        timeout=15,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    product_links = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = clean_text(link.get_text(" ", strip=True))

        if "/products/" not in href:
            continue

        if "LKR" not in text:
            continue

        full_url = href
        if href.startswith("/"):
            full_url = f"https://incarnage.com{href}"

        title = extract_title(text)
        price = extract_price(text)

        if not title:
            continue

        is_sold_out = "sold out" in text.lower()

        product_links.append({
            "title": title,
            "price": price,
            "product_url": full_url,
            "availability": not is_sold_out
        })

    # remove duplicates by product_url
    unique_products = []
    seen_urls = set()

    for item in product_links:
        if item["product_url"] in seen_urls:
            continue

        seen_urls.add(item["product_url"])
        unique_products.append(item)

    crawled_products = []

    for item in unique_products[:max_items]:
        detail_data = extract_product_detail_data(item["product_url"])

        color_source_text = detail_data["color_text"] or item["title"]
        description = detail_data["description"] or f"Carnage women's crop top: {item['title']}"

        crawled_products.append({
            "item_id": create_item_id(item["product_url"]),
            "title": item["title"],
            "category": "top",
            "subcategory": "crop_top",
            "color": infer_color_from_title(color_source_text),
            "style": ["casual"],
            "brand": "Carnage",
            "price": item["price"],
            "currency": "LKR",
            "image_url": "https://example.com/carnage-placeholder.jpg",
            "product_url": item["product_url"],
            "source": "carnage",
            "description": description,
            "availability": item["availability"] and detail_data["availability"]
    })

    return crawled_products


def generate_sample_crawled_products(request):
    """
    Stage 1 real crawler.

    This function now crawls the Carnage women's crop tops collection page.
    The function name is kept temporarily to avoid changing the route file again.
    """

    max_items = request.max_items or 10
    return crawl_carnage_crop_tops(max_items=max_items)
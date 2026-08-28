import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


CARNAGE_BASE_URL = "https://incarnage.com"
CARNAGE_PLACEHOLDER_IMAGE_URL = "https://example.com/carnage-placeholder.jpg"

# These are the Carnage women clothing collection pages we crawl.
# The crawler automatically adds:
# filter.v.availability=1
# so only available products are collected from collection pages.
CARNAGE_COLLECTIONS = [
    {
        "name": "crop_tops",
        "url": "https://incarnage.com/collections/womens-crop-tops",
        "category": "top",
        "subcategory": "crop_top",
        "extra_styles": ["casual"],
    },
    {
        "name": "leggings",
        "url": "https://incarnage.com/collections/womens-leggings",
        "category": "leggings",
        "subcategory": "leggings",
        "extra_styles": ["activewear", "athleisure"],
    },
    {
        "name": "skirts",
        "url": "https://incarnage.com/collections/skirts",
        "category": "skirt",
        "subcategory": "skirt",
        "extra_styles": ["casual"],
    },
    {
        "name": "shorts",
        "url": "https://incarnage.com/collections/womens-shorts-1",
        "category": "shorts",
        "subcategory": "shorts",
        "extra_styles": ["casual", "activewear"],
    },
    {
        "name": "jeans",
        "url": "https://incarnage.com/collections/womens-jeans",
        "category": "jeans",
        "subcategory": "jeans",
        "extra_styles": ["denim", "casual"],
    },
    {
        "name": "joggers_pants",
        "url": "https://incarnage.com/collections/womens-joggers-pants",
        "category": "pants",
        "subcategory": "joggers",
        "extra_styles": ["activewear", "athleisure", "casual"],
    },
]


COLOR_ALIASES = {
    "black": ["black", "jet black"],
    "white": ["white", "sheer white", "off white", "ivory"],
    "brown": ["brown", "mocha", "coffee", "chocolate", "espresso"],
    "grey": ["grey", "gray", "slate grey", "charcoal", "silver"],
    "green": ["green", "olive", "sage", "mint"],
    "blue": ["blue", "navy", "sky blue", "light blue", "denim"],
    "red": ["red", "burgundy", "maroon", "wine", "crimson"],
    "pink": ["pink", "vintage rose", "serene pink", "rose", "blush"],
    "beige": ["beige", "cream", "nude", "sand", "khaki"],
    "purple": ["purple", "lilac", "lavender", "plum"],
    "yellow": ["yellow", "butter yellow", "mustard"],
    "orange": ["orange", "rust", "terracotta"],
    "multi": [
        "multi",
        "multicolor",
        "multi color",
        "print",
        "printed",
        "floral",
        "stripe",
        "striped",
        "pattern",
    ],
}


CATEGORY_KEYWORDS = [
    ("top", "crop_top", ["crop top", "crop tee", "baby tee", "tee", "t-shirt", "tshirt", "top", "polo"]),
    ("leggings", "leggings", ["legging", "leggings", "tights"]),
    ("skirt", "skirt", ["skirt"]),
    ("shorts", "shorts", ["short", "shorts"]),
    ("jeans", "jeans", ["jean", "jeans", "denim"]),
    ("pants", "joggers", ["jogger", "joggers"]),
    ("pants", "pants", ["pant", "pants", "trouser", "trousers"]),
]


STYLE_KEYWORDS = {
    "activewear": [
        "training",
        "gym",
        "workout",
        "active",
        "activewear",
        "moisture-wicking",
        "moisture wicking",
        "sweat-wicking",
        "sweat wicking",
    ],
    "athleisure": ["athleisure", "jogger", "joggers", "leggings"],
    "lifestyle": ["lifestyle", "everyday", "daily wear", "wardrobe"],
    "seamless": ["seamless"],
    "ribbed": ["ribbed"],
    "fitted": [
        "fitted",
        "sleek",
        "sculpted",
        "body-hugging",
        "body hugging",
        "slim",
        "slim fit",
        "flattering fit",
    ],
    "relaxed": ["relaxed", "loose", "oversized"],
    "smart_casual": ["polo", "collar", "button"],
    "denim": ["denim", "jeans"],
    "casual": ["casual", "easy to wear", "daily wardrobe"],
    "crop": ["crop", "cropped"],
    "high_waist": ["high waist", "high-waist", "high waisted", "high-waisted"],
}


SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
)


def clean_text(text):
    return re.sub(r"\s+", " ", unescape(str(text or ""))).strip()


def remove_emojis(text):
    return re.sub(r"[^\w\s.,/&'()-]", "", text or "").strip()


def strip_html(html_text):
    if not html_text:
        return None

    return BeautifulSoup(str(html_text), "html.parser").get_text(" ", strip=True)


def clean_product_description(description):
    description = strip_html(description)

    if not description:
        return None

    description = clean_text(description)

    # Fix broken page-text prefixes such as "78This crop top..."
    description = re.sub(r"^\d+(?=[A-Za-z])", "", description)

    description = re.sub(
        r"^(?:Description|Product\s+details?:?|Key Features:?)\s*",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = clean_text(description).strip(" -:|")

    return description or None


def slugify(value):
    value = clean_text(value).lower()
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value)
    return value.strip("_") or "unknown"


def make_absolute_url(url, page_url=CARNAGE_BASE_URL):
    url = clean_text(url)

    if not url:
        return None

    if url.startswith("//"):
        return f"https:{url}"

    return urljoin(page_url, url)


def clean_product_url(product_url):
    absolute_url = make_absolute_url(product_url, CARNAGE_BASE_URL)

    if not absolute_url:
        return None

    parsed_url = urlparse(absolute_url)
    path_parts = [part for part in parsed_url.path.split("/") if part]

    if "products" not in path_parts:
        return None

    product_index = path_parts.index("products")

    if product_index + 1 >= len(path_parts):
        return None

    slug = path_parts[product_index + 1]
    return f"https://incarnage.com/products/{slug}"


def get_product_slug(product_url):
    return urlparse(product_url).path.rstrip("/").split("/")[-1]


def get_product_json_url(product_url):
    slug = get_product_slug(product_url)
    return f"https://incarnage.com/products/{slug}.js"


def add_available_filter(collection_url):
    parsed_url = urlparse(collection_url)
    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))

    query_params["filter.v.availability"] = "1"

    return urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            urlencode(query_params),
            parsed_url.fragment,
        )
    )


def upgrade_shopify_image_quality(image_url, target_width=1600):
    if not image_url:
        return image_url

    absolute_url = make_absolute_url(image_url, CARNAGE_BASE_URL)
    parsed_url = urlparse(absolute_url)
    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))

    query_params["width"] = str(target_width)

    return urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            urlencode(query_params),
            parsed_url.fragment,
        )
    )


def parse_shopify_price(price_value):
    if price_value is None:
        return None

    try:
        price = float(price_value)
    except (TypeError, ValueError):
        return None

    # Shopify commonly stores LKR price as cents.
    # Example: 425000 means LKR 4,250.00
    if price > 100000:
        return round(price / 100, 2)

    return round(price, 2)


def normalize_color_value(color_text):
    if not color_text:
        return None

    color_text = clean_text(color_text).lower()
    color_text = re.sub(r"[^a-z\s/-]", " ", color_text)
    color_text = clean_text(color_text)

    for canonical_color, aliases in COLOR_ALIASES.items():
        for alias in aliases:
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, color_text, flags=re.IGNORECASE):
                return canonical_color

    return None


def normalize_colors_from_text(text):
    matched_colors = []

    for canonical_color, aliases in COLOR_ALIASES.items():
        for alias in aliases:
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, text or "", flags=re.IGNORECASE):
                if canonical_color not in matched_colors:
                    matched_colors.append(canonical_color)
                break

    return matched_colors


def get_option_names(product_json):
    option_names = []

    for option in product_json.get("options", []):
        if isinstance(option, dict):
            option_names.append(clean_text(option.get("name", "")).lower())
        else:
            option_names.append(clean_text(option).lower())

    return option_names


def get_color_option_index(product_json):
    option_names = get_option_names(product_json)

    for index, option_name in enumerate(option_names):
        if "color" in option_name or "colour" in option_name:
            return index

    # Carnage usually uses Color as option1.
    # If option names are missing, use option1 as a safe fallback.
    return 0


def get_variant_option_value(variant, option_index):
    if option_index is None:
        return ""

    option_key = f"option{option_index + 1}"
    return clean_text(variant.get(option_key, ""))


def get_variant_available(variant):
    available = variant.get("available")

    if isinstance(available, bool):
        return available

    return str(available).lower() == "true"


def get_variant_id(variant):
    variant_id = variant.get("id")
    return str(variant_id) if variant_id is not None else None


def get_variant_product_url(product_url, variant):
    variant_id = get_variant_id(variant)

    if not variant_id:
        return product_url

    return f"{product_url}?variant={variant_id}"


def get_variant_image_url(variant, product_json):
    featured_image = variant.get("featured_image")

    if isinstance(featured_image, dict):
        image_url = (
            featured_image.get("src")
            or featured_image.get("url")
            or featured_image.get("preview_image", {}).get("src")
        )

        if image_url:
            return upgrade_shopify_image_quality(image_url)

    if isinstance(featured_image, str) and featured_image:
        return upgrade_shopify_image_quality(featured_image)

    featured_media = variant.get("featured_media")

    if isinstance(featured_media, dict):
        image_url = (
            featured_media.get("src")
            or featured_media.get("preview_image", {}).get("src")
        )

        if image_url:
            return upgrade_shopify_image_quality(image_url)

    product_featured_image = product_json.get("featured_image")

    if product_featured_image:
        return upgrade_shopify_image_quality(product_featured_image)

    for image_url in product_json.get("images", []):
        if image_url:
            return upgrade_shopify_image_quality(image_url)

    return CARNAGE_PLACEHOLDER_IMAGE_URL


def get_best_variant_for_color(variants):
    available_variants = [variant for variant in variants if get_variant_available(variant)]

    for variant in available_variants:
        if variant.get("featured_image") or variant.get("featured_media"):
            return variant

    if available_variants:
        return available_variants[0]

    return None


def group_variants_by_color(product_json):
    variants = product_json.get("variants", [])
    color_option_index = get_color_option_index(product_json)
    grouped_variants = {}

    for variant in variants:
        raw_color_value = get_variant_option_value(variant, color_option_index)

        if not raw_color_value:
            raw_color_value = "unknown"

        color_key = clean_text(raw_color_value).lower()
        grouped_variants.setdefault(color_key, []).append(variant)

    return grouped_variants


def clean_title(title):
    title = remove_emojis(clean_text(title))

    title = re.sub(
        r"\s*(?:\||-|–)\s*CARNAGE.*$",
        "",
        title,
        flags=re.IGNORECASE,
    )

    title = re.split(
        r"(?:LKR|Rs\.?|Rs)\s*[\d,]+(?:\.\d{1,2})?",
        title,
        flags=re.IGNORECASE,
    )[0]

    title = re.sub(
        r"\b(sold out|sale|new|popular|style|best seller|quick view|select options|add to cart)\b",
        "",
        title,
        flags=re.IGNORECASE,
    )

    title = re.sub(r"\d+%\s*off", "", title, flags=re.IGNORECASE)

    return clean_text(title)


def infer_category_from_product(product_json, fallback_category, fallback_subcategory):
    title = clean_text(product_json.get("title", ""))
    product_type = clean_text(product_json.get("type", ""))
    tags = product_json.get("tags", [])

    if isinstance(tags, list):
        tag_text = " ".join(clean_text(tag) for tag in tags)
    else:
        tag_text = clean_text(tags)

    searchable_text = f"{title} {product_type} {tag_text}".lower()

    for category, subcategory, keywords in CATEGORY_KEYWORDS:
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", searchable_text):
                return category, subcategory

    return fallback_category, fallback_subcategory


def infer_styles_from_text(title, description, product_json=None, extra_styles=None):
    extra_styles = extra_styles or []

    product_type = ""
    tags = []

    if product_json:
        product_type = clean_text(product_json.get("type", ""))
        raw_tags = product_json.get("tags", [])

        if isinstance(raw_tags, list):
            tags = [clean_text(tag) for tag in raw_tags]
        else:
            tags = [clean_text(raw_tags)]

    searchable_text = f"{title or ''} {description or ''} {product_type} {' '.join(tags)}".lower()
    styles = ["casual"]

    for style, keywords in STYLE_KEYWORDS.items():
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", searchable_text, flags=re.IGNORECASE):
                styles.append(style)
                break

    styles.extend(extra_styles)

    return list(dict.fromkeys([style for style in styles if style]))


def create_item_id(product_url, color_value=None):
    slug = slugify(get_product_slug(product_url))

    if color_value:
        return f"CARNAGE_{slug}_{slugify(color_value)}"

    return f"CARNAGE_{slug}"


def fetch_product_json(product_url):
    json_url = get_product_json_url(product_url)

    response = SESSION.get(
        json_url,
        timeout=15,
        headers={
            "Accept": "application/json,text/plain,*/*",
        },
    )
    response.raise_for_status()

    return response.json()


def extract_product_links_from_collection(collection_url, max_items):
    filtered_url = add_available_filter(collection_url)

    product_urls = _extract_product_links_from_page(filtered_url, max_items=max_items)

    # Backup: if the availability-filtered collection gives no products,
    # try the normal collection URL. Product JSON availability still filters
    # out unavailable variants later.
    if not product_urls:
        product_urls = _extract_product_links_from_page(collection_url, max_items=max_items)

    return product_urls


def _extract_product_links_from_page(page_url, max_items):
    response = SESSION.get(page_url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    product_urls = []
    seen_urls = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if "/products/" not in href:
            continue

        product_url = clean_product_url(href)

        if not product_url or product_url in seen_urls:
            continue

        seen_urls.add(product_url)
        product_urls.append(product_url)

        if len(product_urls) >= max_items:
            break

    return product_urls


def extract_products_from_shopify_json(product_json, product_url, collection_config):
    if not product_json.get("available", False):
        return []

    title = clean_title(product_json.get("title")) or clean_text(product_json.get("handle"))
    description = (
        clean_product_description(product_json.get("description"))
        or f"Carnage fashion product: {title}"
    )

    category, subcategory = infer_category_from_product(
        product_json=product_json,
        fallback_category=collection_config["category"],
        fallback_subcategory=collection_config["subcategory"],
    )

    grouped_variants = group_variants_by_color(product_json)

    if not grouped_variants:
        return []

    crawled_products = []

    raw_tags = product_json.get("tags", [])
    if isinstance(raw_tags, list):
        tags_text = " ".join(clean_text(tag) for tag in raw_tags)
    else:
        tags_text = clean_text(raw_tags)

    for color_key, variants in grouped_variants.items():
        selected_variant = get_best_variant_for_color(variants)

        if selected_variant is None:
            continue

        raw_color_value = color_key if color_key != "unknown" else ""
        normalized_color = normalize_color_value(raw_color_value)

        if normalized_color:
            normalized_colors = [normalized_color]
        else:
            normalized_colors = normalize_colors_from_text(
                f"{raw_color_value} {title} {tags_text}"
            )

        if not normalized_colors:
            normalized_colors = ["unknown"]

        availability = any(get_variant_available(variant) for variant in variants)

        if not availability:
            continue

        image_url = get_variant_image_url(selected_variant, product_json)
        price = parse_shopify_price(selected_variant.get("price") or product_json.get("price"))
        variant_product_url = get_variant_product_url(product_url, selected_variant)
        color_for_id = raw_color_value or normalized_colors[0]

        crawled_products.append(
            {
                "item_id": create_item_id(product_url, color_for_id),
                "title": title,
                "category": category,
                "subcategory": subcategory,
                "color": normalized_colors,
                "style": infer_styles_from_text(
                    title=title,
                    description=description,
                    product_json=product_json,
                    extra_styles=collection_config.get("extra_styles", []),
                ),
                "brand": "Carnage",
                "price": price,
                "currency": "LKR",
                "image_url": image_url,
                "product_url": variant_product_url,
                "source": "carnage",
                "description": description,
                "availability": True,
            }
        )

    return crawled_products


def crawl_single_carnage_product(product_url, collection_config):
    try:
        product_json = fetch_product_json(product_url)
        return extract_products_from_shopify_json(
            product_json=product_json,
            product_url=product_url,
            collection_config=collection_config,
        )
    except Exception as error:
        print(f"Carnage product JSON failed for {product_url}: {error}")
        return []


def deduplicate_products(products):
    unique_products = []
    seen_item_ids = set()

    for product in products:
        item_id = product.get("item_id")

        if not item_id or item_id in seen_item_ids:
            continue

        seen_item_ids.add(item_id)
        unique_products.append(product)

    return unique_products


def crawl_carnage_products(max_items=10):
    """
    Crawls multiple Carnage women clothing collections using Shopify product JSON.

    Important:
    - max_items means max product URLs per collection.
    - Only available products/variants are returned.
    - Products are de-duplicated by product URL and final item_id.
    - One DB row is returned per available color variant.
    """

    max_items = max_items or 10
    all_products = []
    seen_product_urls = set()

    for collection_config in CARNAGE_COLLECTIONS:
        collection_url = collection_config["url"]

        try:
            product_urls = extract_product_links_from_collection(
                collection_url=collection_url,
                max_items=max_items,
            )
        except Exception as error:
            print(f"Carnage collection failed: {collection_config['name']} - {error}")
            continue

        for product_url in product_urls:
            if product_url in seen_product_urls:
                continue

            seen_product_urls.add(product_url)

            product_variants = crawl_single_carnage_product(
                product_url=product_url,
                collection_config=collection_config,
            )
            all_products.extend(product_variants)

    unique_products = deduplicate_products(all_products)
    print(f"Carnage crawler success: {len(unique_products)} available products")

    return unique_products


def crawl_carnage_all_clothing(max_items=10):
    return crawl_carnage_products(max_items=max_items)


# Keep this old function name because crawler_service.py already imports it.
# After replacing this file, your existing backend can still call
# crawl_carnage_crop_tops(), but it will now collect all configured
# Carnage women clothing categories.
def crawl_carnage_crop_tops(max_items=10):
    return crawl_carnage_products(max_items=max_items)
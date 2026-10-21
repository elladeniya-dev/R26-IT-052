import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


GFLOCK_BASE_URL = "https://gflock.lk"
GFLOCK_PLACEHOLDER_IMAGE_URL = "https://example.com/gflock-placeholder.jpg"

# These are the Gflock clothing collection pages we crawl.
# The crawler automatically adds:
# sort_by=created-descending&filter.v.availability=1
# so only available products are collected from collection pages.
GFLOCK_COLLECTIONS = [
    {
        "name": "new_in",
        "url": "https://gflock.lk/collections/new-products",
        "category": "fashion",
        "subcategory": "new_arrivals",
        "extra_styles": ["new_in"],
    },
    {
        "name": "work_wear",
        "url": "https://gflock.lk/collections/work-wear-collection-4",
        "category": "fashion",
        "subcategory": "work_wear",
        "extra_styles": ["formal", "workwear", "smart_casual"],
    },
    {
        "name": "casual_wear",
        "url": "https://gflock.lk/collections/product-directory-casual",
        "category": "fashion",
        "subcategory": "casual_wear",
        "extra_styles": ["casual"],
    },
    {
        "name": "party",
        "url": "https://gflock.lk/collections/party",
        "category": "fashion",
        "subcategory": "party_wear",
        "extra_styles": ["party", "evening"],
    },
    {
        "name": "natural_blends",
        "url": "https://gflock.lk/collections/cotton",
        "category": "fashion",
        "subcategory": "natural_blends",
        "extra_styles": ["natural_blends", "cotton"],
    },
    {
        "name": "tops",
        "url": "https://gflock.lk/collections/tops",
        "category": "top",
        "subcategory": "top",
        "extra_styles": [],
    },
    {
        "name": "dresses",
        "url": "https://gflock.lk/collections/dresses",
        "category": "dress",
        "subcategory": "dress",
        "extra_styles": [],
    },
    {
        "name": "pants",
        "url": "https://gflock.lk/collections/women-trousers",
        "category": "pants",
        "subcategory": "trousers",
        "extra_styles": [],
    },
    {
        "name": "blazers",
        "url": "https://gflock.lk/collections/blazers",
        "category": "blazer",
        "subcategory": "blazer",
        "extra_styles": ["formal", "smart_casual"],
    },
    {
        "name": "jeans",
        "url": "https://gflock.lk/collections/women-jeans",
        "category": "jeans",
        "subcategory": "jeans",
        "extra_styles": ["denim", "casual"],
    },
    {
        "name": "jumpsuits",
        "url": "https://gflock.lk/collections/jumpsuits-playsuits",
        "category": "jumpsuit",
        "subcategory": "jumpsuit",
        "extra_styles": [],
    },
    {
        "name": "shorts",
        "url": "https://gflock.lk/collections/women-shorts",
        "category": "shorts",
        "subcategory": "shorts",
        "extra_styles": ["casual"],
    },
]


COLOR_ALIASES = {
    "black": ["black", "jet black"],
    "white": ["white", "ivory", "sheer white", "off white"],
    "brown": ["brown", "chocolate", "mocha", "coffee"],
    "grey": ["grey", "gray", "charcoal", "silver"],
    "green": ["green", "sage", "olive", "mint"],
    "blue": ["blue", "navy", "denim", "sky blue", "light blue"],
    "red": ["red", "maroon", "burgundy", "wine", "crimson"],
    "pink": ["pink", "rose", "vintage rose", "serene pink", "blush"],
    "beige": ["beige", "cream", "nude", "sand", "khaki", "natural"],
    "purple": ["purple", "lilac", "lavender", "plum"],
    "yellow": ["yellow", "mustard", "butter yellow"],
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
    ("dress", "dress", ["dress", "dresses", "midi dress", "maxi dress", "mini dress"]),
    ("top", "top", ["top", "tops", "tee", "t-shirt", "tshirt", "shirt", "blouse", "camisole", "tank"]),
    ("pants", "trousers", ["trouser", "trousers", "pant", "pants", "wide leg", "culotte"]),
    ("blazer", "blazer", ["blazer"]),
    ("jeans", "jeans", ["jean", "jeans", "denim pant", "denim pants"]),
    ("jumpsuit", "jumpsuit", ["jumpsuit", "playsuit", "romper"]),
    ("shorts", "shorts", ["short", "shorts"]),
    ("skirt", "skirt", ["skirt"]),
]


STYLE_KEYWORDS = {
    "formal": ["formal", "office", "workwear", "work wear", "work-wear", "boardroom"],
    "party": ["party", "evening", "cocktail", "occasion", "after dusk"],
    "summer": ["summer", "linen", "sleeveless"],
    "floral": ["floral", "flower", "print", "printed"],
    "fitted": ["fitted", "bodycon", "slim", "sculpted", "tailored"],
    "relaxed": ["relaxed", "flowy", "loose", "oversized"],
    "smart_casual": ["shirt dress", "collar", "button", "blazer", "tailored"],
    "maxi": ["maxi"],
    "midi": ["midi"],
    "mini": ["mini"],
    "denim": ["denim", "jeans"],
    "cotton": ["cotton"],
    "natural_blends": ["natural blend", "natural blends", "linen", "cotton"],
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
    description = re.sub(
        r"^(?:Description|Product\s+details?):?\s*",
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


def make_absolute_url(url, page_url=GFLOCK_BASE_URL):
    url = clean_text(url)

    if not url:
        return None

    if url.startswith("//"):
        return f"https:{url}"

    return urljoin(page_url, url)


def clean_product_url(product_url):
    absolute_url = make_absolute_url(product_url, GFLOCK_BASE_URL)

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
    return f"https://gflock.lk/products/{slug}"


def get_product_slug(product_url):
    return urlparse(product_url).path.rstrip("/").split("/")[-1]


def get_product_json_url(product_url):
    slug = get_product_slug(product_url)
    return f"https://gflock.lk/products/{slug}.js"


def add_available_filter(collection_url):
    parsed_url = urlparse(collection_url)
    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))

    query_params["sort_by"] = "created-descending"
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

    absolute_url = make_absolute_url(image_url, GFLOCK_BASE_URL)
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
    # Example: 1180000 means LKR 11,800.00
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

    return None


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

    return GFLOCK_PLACEHOLDER_IMAGE_URL


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
        r"\s*(?:\||-|–)\s*Gflock.*$",
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
        r"\b(sold out|sale|new|quick view|select options|add to cart)\b",
        "",
        title,
        flags=re.IGNORECASE,
    )
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

    tags = []
    product_type = ""

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
        return f"GFLOCK_{slug}_{slugify(color_value)}"

    return f"GFLOCK_{slug}"


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

    response = SESSION.get(filtered_url, timeout=20)
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
        or f"Gflock fashion product: {title}"
    )

    category, subcategory = infer_category_from_product(
        product_json=product_json,
        fallback_category=collection_config["category"],
        fallback_subcategory=collection_config["subcategory"],
    )

    grouped_variants = group_variants_by_color(product_json)
    crawled_products = []

    if not grouped_variants:
        return []

    for color_key, variants in grouped_variants.items():
        selected_variant = get_best_variant_for_color(variants)

        if selected_variant is None:
            continue

        raw_color_value = color_key if color_key != "unknown" else ""
        normalized_color = normalize_color_value(raw_color_value)

        if not normalized_color:
            normalized_colors = normalize_colors_from_text(
                f"{raw_color_value} {title} {' '.join(product_json.get('tags', []))}"
            )
        else:
            normalized_colors = [normalized_color]

        if not normalized_colors:
            normalized_colors = ["unknown"]

        image_url = get_variant_image_url(selected_variant, product_json)
        price = parse_shopify_price(selected_variant.get("price") or product_json.get("price"))
        variant_product_url = get_variant_product_url(product_url, selected_variant)
        availability = any(get_variant_available(variant) for variant in variants)

        if not availability:
            continue

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
                "brand": "Gflock",
                "price": price,
                "currency": "LKR",
                "image_url": image_url,
                "product_url": variant_product_url,
                "source": "gflock",
                "description": description,
                "availability": True,
            }
        )

    return crawled_products


def crawl_single_gflock_product(product_url, collection_config):
    try:
        product_json = fetch_product_json(product_url)
        return extract_products_from_shopify_json(
            product_json=product_json,
            product_url=product_url,
            collection_config=collection_config,
        )
    except Exception as error:
        print(f"Gflock product JSON failed for {product_url}: {error}")
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


def crawl_gflock_products(max_items=10):
    """
    Crawls multiple Gflock clothing collections using Shopify product JSON.

    Important:
    - max_items means max product URLs per collection.
    - Only available products/variants are returned.
    - Products are de-duplicated by product URL and final item_id.
    - One DB row is returned per available color variant.
    """

    max_items = max_items or 10
    all_products = []
    seen_product_urls = set()

    for collection_config in GFLOCK_COLLECTIONS:
        collection_url = collection_config["url"]

        try:
            product_urls = extract_product_links_from_collection(
                collection_url=collection_url,
                max_items=max_items,
            )
        except Exception as error:
            print(f"Gflock collection failed: {collection_config['name']} - {error}")
            continue

        for product_url in product_urls:
            if product_url in seen_product_urls:
                continue

            seen_product_urls.add(product_url)
            product_variants = crawl_single_gflock_product(
                product_url=product_url,
                collection_config=collection_config,
            )
            all_products.extend(product_variants)

    unique_products = deduplicate_products(all_products)
    print(f"Gflock crawler success: {len(unique_products)} available products")

    return unique_products


def crawl_gflock_all_clothing(max_items=10):
    return crawl_gflock_products(max_items=max_items)


# Keep this old function name because crawler_service.py already imports it.
# After replacing this file, your existing backend can still call crawl_gflock_dresses(),
# but it will now collect all configured Gflock clothing categories.
def crawl_gflock_dresses(max_items=10):
    return crawl_gflock_products(max_items=max_items)
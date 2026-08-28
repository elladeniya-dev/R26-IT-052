import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


BELLINI_BASE_URL = "https://www.bellini.lk"
BELLINI_PLACEHOLDER_IMAGE_URL = "https://example.com/bellini-placeholder.jpg"

BELLINI_COLLECTIONS = [
    {
        "name": "tops",
        "url": "https://www.bellini.lk/collections/top",
        "category": "top",
        "subcategory": "top",
        "extra_styles": ["casual"],
    },
    {
        "name": "dresses",
        "url": "https://www.bellini.lk/collections/dresses",
        "category": "dress",
        "subcategory": "dress",
        "extra_styles": ["casual", "elegant"],
    },
    {
        "name": "pants",
        "url": "https://www.bellini.lk/collections/pant",
        "category": "pants",
        "subcategory": "pants",
        "extra_styles": ["casual"],
    },
    {
        "name": "skirts",
        "url": "https://www.bellini.lk/collections/skirts",
        "category": "skirt",
        "subcategory": "skirt",
        "extra_styles": ["casual"],
    },
    {
        "name": "shorts",
        "url": "https://www.bellini.lk/collections/shorts",
        "category": "shorts",
        "subcategory": "shorts",
        "extra_styles": ["casual", "summer"],
    },
]


COLOR_ALIASES = {
    "black": ["black", "jet black"],
    "white": ["white", "off white", "ivory"],
    "red": ["red", "maroon", "burgundy", "wine"],
    "blue": ["blue", "navy", "navy blue", "dark blue", "light blue", "denim"],
    "green": ["green", "olive", "sage", "mint"],
    "pink": ["pink", "baby pink", "rose", "blush"],
    "beige": ["beige", "cream", "nude", "sand", "khaki", "natural"],
    "grey": ["grey", "gray", "charcoal", "silver"],
    "brown": ["brown", "mocha", "coffee", "chocolate", "tan"],
    "yellow": ["yellow", "mustard"],
    "orange": ["orange", "rust", "terracotta"],
    "purple": ["purple", "lilac", "lavender"],
    "multi": [
        "multi",
        "multi color",
        "multicolor",
        "printed",
        "print",
        "floral",
        "stripe",
        "striped",
        "pattern",
    ],
}


CATEGORY_KEYWORDS = [
    ("dress", "dress", ["dress", "mini dress", "midi dress", "maxi dress"]),
    ("top", "shirt", ["shirt", "button down", "blouse"]),
    ("top", "blazer", ["blazer", "waistcoat", "jacket"]),
    ("top", "tshirt", ["tshirt", "t-shirt", "tee", "sweatshirt", "hoodie"]),
    ("top", "top", ["top", "crop", "tube top", "camisole"]),
    ("pants", "pants", ["pant", "pants", "trouser", "trousers"]),
    ("jeans", "jeans", ["jean", "jeans", "denim"]),
    ("skirt", "skirt", ["skirt"]),
    ("shorts", "shorts", ["short", "shorts"]),
]


STYLE_KEYWORDS = {
    "formal": ["formal", "office", "workwear", "work wear", "blazer", "waistcoat", "tailored"],
    "smart_casual": ["shirt", "button", "button down", "collar", "blazer", "waistcoat"],
    "casual": ["casual", "everyday", "daily", "relaxed", "sweatshirt", "hoodie"],
    "party": ["party", "evening", "cocktail", "occasion"],
    "elegant": ["elegant", "satin", "lace", "wrap", "pleated"],
    "minimal": ["minimal", "basic", "plain", "solid", "classic", "clean"],
    "trendy": ["trendy", "new", "new arrival", "fashion", "crop", "tube"],
    "summer": ["summer", "sleeveless", "tube", "crop"],
    "floral": ["floral", "flower", "printed", "print"],
    "denim": ["denim", "jeans"],
    "fitted": ["bodycon", "fitted", "slim", "stretch", "tube"],
    "relaxed": ["relaxed", "oversized", "loose"],
    "maxi": ["maxi"],
    "midi": ["midi"],
    "mini": ["mini"],
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
        r"^(?:Description|Product\s+details?|Product\s+information):?\s*",
        "",
        description,
        flags=re.IGNORECASE,
    )

    return clean_text(description).strip(" -:|") or None


def slugify(value):
    value = clean_text(value).lower()
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value)
    return value.strip("_") or "unknown"


def make_absolute_url(url, page_url=BELLINI_BASE_URL):
    url = clean_text(url)

    if not url:
        return None

    if url.startswith("//"):
        return f"https:{url}"

    return urljoin(page_url, url)


def clean_product_url(product_url):
    absolute_url = make_absolute_url(product_url, BELLINI_BASE_URL)

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
    return f"https://www.bellini.lk/products/{slug}"


def get_product_slug(product_url):
    return urlparse(product_url).path.rstrip("/").split("/")[-1]


def get_product_json_url(product_url):
    slug = get_product_slug(product_url)
    return f"https://www.bellini.lk/products/{slug}.js"


def add_available_filter(collection_url, page_number=1):
    parsed_url = urlparse(collection_url)
    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))

    query_params["filter.v.availability"] = "1"
    query_params["sort_by"] = "created-descending"

    if page_number > 1:
        query_params["page"] = str(page_number)

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

    absolute_url = make_absolute_url(image_url, BELLINI_BASE_URL)
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

    if price > 100000:
        return round(price / 100, 2)

    return round(price, 2)


def parse_price_from_text(text):
    if not text:
        return None

    match = re.search(
        r"(?:Rs\.?|LKR)\s*([\d,]+(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


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

    return clean_text(variant.get(f"option{option_index + 1}", ""))


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

    product_featured_image = product_json.get("featured_image")

    if product_featured_image:
        return upgrade_shopify_image_quality(product_featured_image)

    for image_url in product_json.get("images", []):
        if image_url:
            return upgrade_shopify_image_quality(image_url)

    return BELLINI_PLACEHOLDER_IMAGE_URL


def get_best_available_variant(variants):
    available_variants = [variant for variant in variants if get_variant_available(variant)]

    for variant in available_variants:
        if variant.get("featured_image"):
            return variant

    if available_variants:
        return available_variants[0]

    return None


def group_variants_by_color(product_json, fallback_color):
    variants = product_json.get("variants", [])
    color_option_index = get_color_option_index(product_json)

    if color_option_index is None:
        return {fallback_color or "unknown": variants}

    grouped_variants = {}

    for variant in variants:
        raw_color_value = get_variant_option_value(variant, color_option_index)

        if not raw_color_value:
            raw_color_value = fallback_color or "unknown"

        color_key = clean_text(raw_color_value).lower()
        grouped_variants.setdefault(color_key, []).append(variant)

    return grouped_variants


def clean_title(title):
    title = remove_emojis(clean_text(title))

    title = re.sub(
        r"\s*(?:\||-|–)\s*Bellini.*$",
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
        r"\b(sold out|out of stock|in stock|sale|new|quick view|select options|add to cart|add)\b",
        "",
        title,
        flags=re.IGNORECASE,
    )

    return clean_text(title)


def get_tags_text(product_json):
    raw_tags = product_json.get("tags", [])

    if isinstance(raw_tags, list):
        return " ".join(clean_text(tag) for tag in raw_tags)

    return clean_text(raw_tags)


def infer_category_from_product(product_json, fallback_category, fallback_subcategory):
    title = clean_text(product_json.get("title", ""))
    product_type = clean_text(product_json.get("type", ""))
    tags_text = get_tags_text(product_json)
    description = clean_product_description(product_json.get("description")) or ""

    searchable_text = f"{title} {product_type} {tags_text} {description}".lower()

    for category, subcategory, keywords in CATEGORY_KEYWORDS:
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", searchable_text):
                return category, subcategory

    return fallback_category, fallback_subcategory


def infer_styles_from_text(title, description, product_json=None, extra_styles=None):
    extra_styles = extra_styles or []

    product_type = ""
    tags_text = ""

    if product_json:
        product_type = clean_text(product_json.get("type", ""))
        tags_text = get_tags_text(product_json)

    searchable_text = f"{title or ''} {description or ''} {product_type} {tags_text}".lower()
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

    if color_value and color_value != "unknown":
        return f"BELLINI_{slug}_{slugify(color_value)}"

    return f"BELLINI_{slug}"


def fetch_product_json(product_url):
    json_url = get_product_json_url(product_url)

    response = SESSION.get(
        json_url,
        timeout=15,
        headers={"Accept": "application/json,text/plain,*/*"},
    )
    response.raise_for_status()

    return response.json()


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


def extract_product_links_from_collection(collection_url, max_items):
    product_urls = []
    seen_urls = set()

    for page_number in range(1, 4):
        filtered_url = add_available_filter(collection_url, page_number=page_number)

        try:
            page_product_urls = _extract_product_links_from_page(
                page_url=filtered_url,
                max_items=max_items,
            )
        except Exception as error:
            print(f"Bellini collection page failed: {filtered_url} - {error}")
            page_product_urls = []

        if page_number == 1 and not page_product_urls:
            try:
                page_product_urls = _extract_product_links_from_page(
                    page_url=collection_url,
                    max_items=max_items,
                )
            except Exception as error:
                print(f"Bellini backup collection failed: {collection_url} - {error}")
                page_product_urls = []

        for product_url in page_product_urls:
            if product_url in seen_urls:
                continue

            seen_urls.add(product_url)
            product_urls.append(product_url)

            if len(product_urls) >= max_items:
                return product_urls

        if not page_product_urls:
            break

    return product_urls


def extract_products_from_shopify_json(product_json, product_url, collection_config):
    variants = product_json.get("variants", [])

    if not product_json.get("available", False) and not any(
        get_variant_available(variant) for variant in variants
    ):
        return []

    title = clean_title(product_json.get("title")) or clean_text(product_json.get("handle"))
    description = (
        clean_product_description(product_json.get("description"))
        or f"Bellini fashion product: {title}"
    )

    tags_text = get_tags_text(product_json)

    normalized_colors = normalize_colors_from_text(
        f"{title} {description} {tags_text}"
    )

    fallback_color = normalized_colors[0] if normalized_colors else "unknown"

    category, subcategory = infer_category_from_product(
        product_json=product_json,
        fallback_category=collection_config["category"],
        fallback_subcategory=collection_config["subcategory"],
    )

    grouped_variants = group_variants_by_color(product_json, fallback_color)

    if not grouped_variants:
        return []

    crawled_products = []

    for color_key, color_variants in grouped_variants.items():
        selected_variant = get_best_available_variant(color_variants)

        if selected_variant is None:
            continue

        availability = any(get_variant_available(variant) for variant in color_variants)

        if not availability:
            continue

        raw_color_value = color_key if color_key != "unknown" else fallback_color

        current_normalized_colors = normalize_colors_from_text(
            f"{raw_color_value} {title} {description} {tags_text}"
        )

        if not current_normalized_colors:
            current_normalized_colors = normalized_colors or ["unknown"]

        price = parse_shopify_price(selected_variant.get("price") or product_json.get("price"))

        if price is None:
            price = parse_price_from_text(description)

        image_url = get_variant_image_url(selected_variant, product_json)
        variant_product_url = get_variant_product_url(product_url, selected_variant)

        crawled_products.append(
            {
                "item_id": create_item_id(product_url, raw_color_value),
                "title": title,
                "category": category,
                "subcategory": subcategory,
                "color": current_normalized_colors,
                "style": infer_styles_from_text(
                    title=title,
                    description=description,
                    product_json=product_json,
                    extra_styles=collection_config.get("extra_styles", []),
                ),
                "brand": "Bellini",
                "price": price,
                "currency": "LKR",
                "image_url": image_url,
                "product_url": variant_product_url,
                "source": "bellini",
                "description": description,
                "availability": True,
            }
        )

    return crawled_products


def crawl_single_bellini_product(product_url, collection_config):
    try:
        product_json = fetch_product_json(product_url)

        return extract_products_from_shopify_json(
            product_json=product_json,
            product_url=product_url,
            collection_config=collection_config,
        )
    except Exception as error:
        print(f"Bellini product JSON failed for {product_url}: {error}")
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


def crawl_bellini_products(max_items=10):
    """
    Crawls Bellini clothing collections.

    Important:
    - max_items means max product URLs per collection.
    - Collection URLs are requested with filter.v.availability=1.
    - Product JSON availability is checked again before saving.
    - Products are de-duplicated by item_id.
    """

    max_items = max_items or 10
    all_products = []
    seen_product_urls = set()

    for collection_config in BELLINI_COLLECTIONS:
        product_urls = extract_product_links_from_collection(
            collection_url=collection_config["url"],
            max_items=max_items,
        )

        for product_url in product_urls:
            if product_url in seen_product_urls:
                continue

            seen_product_urls.add(product_url)

            product_variants = crawl_single_bellini_product(
                product_url=product_url,
                collection_config=collection_config,
            )

            all_products.extend(product_variants)

    unique_products = deduplicate_products(all_products)
    print(f"Bellini crawler success: {len(unique_products)} available products")

    return unique_products


def crawl_bellini_all_clothing(max_items=10):
    return crawl_bellini_products(max_items=max_items)
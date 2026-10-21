import json
import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


KELLY_FELDER_DRESSES_URL = "https://kellyfelder.com/collections/dresses"
KELLY_FELDER_PLACEHOLDER_IMAGE_URL = "https://example.com/kelly-felder-placeholder.jpg"


COLOR_ALIASES = {
    "black": ["black"],
    "white": ["white", "ivory"],
    "brown": ["brown", "dark brown", "light brown", "chocolate", "mocha"],
    "grey": ["grey", "gray", "charcoal"],
    "green": ["green", "olive", "sage", "mint"],
    "blue": ["blue", "navy", "dark navy", "light blue", "teal"],
    "red": ["red", "maroon", "burgundy", "wine", "crimson"],
    "pink": ["pink", "light pink", "dull pink", "rose", "blush"],
    "beige": ["beige", "cream", "nude", "khaki", "sand"],
    "purple": ["purple", "lilac", "lavender", "plum"],
    "yellow": ["yellow", "mustard"],
    "orange": ["orange", "rust"],
    "multi": [
        "printed",
        "print",
        "floral",
        "striped",
        "stripe",
        "multi",
        "multicolor",
        "multi color",
    ],
}


def clean_text(text):
    return re.sub(r"\s+", " ", unescape(str(text or ""))).strip()


def remove_emojis(text):
    return re.sub(
        r"[^\w\s.,/&'()-]",
        "",
        text or "",
    ).strip()


def clean_product_description(description):
    if not description:
        return None

    description = BeautifulSoup(str(description), "html.parser").get_text(" ", strip=True)
    description = clean_text(description)

    description = re.sub(
        r"^(?:Description|Product\s+details?):?\s*",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = clean_text(description).strip(" -:|")

    return description or None


def clean_title(title):
    title = remove_emojis(clean_text(title))

    title = re.split(
        r"(?:Regular price|Sale price|Rs\.?|LKR|₨)\s*[\d,]+(?:\.\d{1,2})?",
        title,
        flags=re.IGNORECASE,
    )[0]

    title = re.sub(
        r"\b(sold out|sale|new|quick view|add to cart|select options)\b",
        "",
        title,
        flags=re.IGNORECASE,
    )

    return clean_text(title)


def make_absolute_url(url, page_url):
    url = clean_text(url)

    if url.startswith("//"):
        return f"https:{url}"

    return urljoin(page_url, url)


def clean_product_url(product_url):
    """
    Kelly Felder product links can appear as:
    /collections/dresses/products/product-slug
    /products/product-slug

    We force them to:
    https://kellyfelder.com/products/product-slug
    """
    absolute_url = make_absolute_url(product_url, KELLY_FELDER_DRESSES_URL)
    parsed_url = urlparse(absolute_url)
    path_parts = [part for part in parsed_url.path.split("/") if part]

    if "products" not in path_parts:
        return None

    product_index = path_parts.index("products")

    if product_index + 1 >= len(path_parts):
        return None

    slug = path_parts[product_index + 1]

    return f"https://kellyfelder.com/products/{slug}"


def get_product_slug(product_url):
    return urlparse(product_url).path.rstrip("/").split("/")[-1]


def create_item_id(product_url, variant_color=None, variant_id=None):
    slug = get_product_slug(product_url)
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", slug).strip("_").lower()

    if variant_color:
        color_slug = re.sub(
            r"[^a-zA-Z0-9_]+",
            "_",
            variant_color,
        ).strip("_").lower()

        return f"KELLY_FELDER_{slug}_{color_slug}"

    if variant_id:
        return f"KELLY_FELDER_{slug}_{variant_id}"

    return f"KELLY_FELDER_{slug}"


def title_from_url(product_url):
    slug = get_product_slug(product_url)
    return clean_text(slug.replace("-", " ").replace("_", " ")).title()


def upgrade_shopify_image_quality(image_url, target_width=1600):
    """
    Shopify image URLs often contain width=300.
    That looks blurry in the mobile app, so we upgrade it.
    """
    if not image_url:
        return image_url

    parsed_url = urlparse(image_url)

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


def parse_price_value(price_text):
    if price_text is None:
        return None

    price_text = str(price_text)
    price_text = price_text.replace(",", "")
    price_text = price_text.replace("Rs.", "")
    price_text = price_text.replace("Rs", "")
    price_text = price_text.replace("LKR", "")
    price_text = price_text.replace("₨", "")
    price_text = clean_text(price_text)

    try:
        return float(price_text)
    except ValueError:
        return None


def parse_shopify_variant_price(price_value):
    """
    Shopify JSON usually returns price as cents.
    Example: 859000 means Rs 8,590.00
    """
    if price_value is None:
        return None

    try:
        price = float(price_value)
    except (TypeError, ValueError):
        return None

    if price > 100000:
        return round(price / 100, 2)

    return round(price, 2)


def extract_price(text):
    text = text or ""

    price_patterns = [
        r"(?:Regular price|Sale price)\s*(?:Rs\.?|LKR|₨)?\s*([\d,]+(?:\.\d{1,2})?)",
        r"(?:Rs\.?|LKR|₨)\s*([\d,]+(?:\.\d{1,2})?)",
    ]

    prices = []

    for pattern in price_patterns:
        for price_match in re.finditer(pattern, text, flags=re.IGNORECASE):
            price = parse_price_value(price_match.group(1))
            if price is not None:
                prices.append(price)

    if not prices:
        return None

    return min(prices)


def extract_colors_from_text(text, allow_long_text=False):
    if not text:
        return []

    text = clean_text(text)

    if not allow_long_text and len(text) > 140:
        return []

    matched_colors = []

    for canonical_color, aliases in COLOR_ALIASES.items():
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", text, flags=re.IGNORECASE):
                if canonical_color not in matched_colors:
                    matched_colors.append(canonical_color)
                break

    return matched_colors


def infer_color_from_text(title, description):
    searchable_text = f"{title or ''} {description or ''}"
    matched_colors = extract_colors_from_text(searchable_text, allow_long_text=False)

    return matched_colors if matched_colors else ["unknown"]


def infer_styles_from_text(title, description):
    searchable_text = f"{title or ''} {description or ''}".lower()
    styles = ["casual"]

    style_keywords = {
        "formal": [
            "formal",
            "office",
            "workwear",
            "work wear",
            "boardroom",
            "professional",
            "executive",
        ],
        "party": ["party", "evening", "cocktail", "occasion", "after dusk"],
        "summer": ["summer", "linen", "sleeveless"],
        "floral": ["floral", "flower", "printed"],
        "fitted": ["fitted", "body fitted", "bodycon", "slim", "tailored", "column"],
        "relaxed": ["relaxed", "flowy", "loose"],
        "smart_casual": [
            "shirt dress",
            "collar",
            "blazer-style",
            "shawl collar",
            "polo",
        ],
        "maxi": ["maxi"],
        "midi": ["midi"],
        "mini": ["mini"],
        "skater": ["skater"],
        "striped": ["stripe", "striped"],
    }

    for style, keywords in style_keywords.items():
        for keyword in keywords:
            pattern = rf"(?<![a-zA-Z]){re.escape(keyword)}(?![a-zA-Z])"

            if re.search(pattern, searchable_text, flags=re.IGNORECASE):
                styles.append(style)
                break

    return list(dict.fromkeys(styles))


def get_product_json_url(product_url):
    slug = get_product_slug(product_url)
    return f"https://kellyfelder.com/products/{slug}.js"


def fetch_product_json(product_url):
    json_url = get_product_json_url(product_url)

    response = requests.get(
        json_url,
        timeout=15,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )

    response.raise_for_status()
    return response.json()


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

    # Kelly Felder commonly uses color as option1.
    return 0


def get_variant_option_value(variant, option_index):
    option_key = f"option{option_index + 1}"
    return clean_text(variant.get(option_key, ""))


def normalize_variant_color(color_value):
    colors = extract_colors_from_text(color_value, allow_long_text=True)

    if not colors:
        return ["unknown"]

    return colors


def get_variant_image_url(variant, product_json):
    featured_image = variant.get("featured_image")

    if isinstance(featured_image, dict):
        image_url = (
            featured_image.get("src")
            or featured_image.get("url")
            or featured_image.get("preview_image", {}).get("src")
        )

        if image_url:
            return upgrade_shopify_image_quality(
                make_absolute_url(image_url, "https://kellyfelder.com")
            )

    featured_image = variant.get("featured_image")

    if isinstance(featured_image, str) and featured_image:
        return upgrade_shopify_image_quality(
            make_absolute_url(featured_image, "https://kellyfelder.com")
        )

    product_featured_image = product_json.get("featured_image")

    if product_featured_image:
        return upgrade_shopify_image_quality(
            make_absolute_url(product_featured_image, "https://kellyfelder.com")
        )

    images = product_json.get("images", [])

    if images:
        return upgrade_shopify_image_quality(
            make_absolute_url(images[0], "https://kellyfelder.com")
        )

    return KELLY_FELDER_PLACEHOLDER_IMAGE_URL


def get_variant_available(variant):
    available = variant.get("available")

    if isinstance(available, bool):
        return available

    if str(available).lower() == "true":
        return True

    if str(available).lower() == "false":
        return False

    return False


def get_variant_id(variant):
    variant_id = variant.get("id")

    if variant_id is None:
        return None

    return str(variant_id)


def get_variant_product_url(product_url, variant):
    variant_id = get_variant_id(variant)

    if not variant_id:
        return product_url

    return f"{product_url}?variant={variant_id}"


def get_best_variant_for_color(variants):
    """
    A product color usually has multiple size variants.
    We store one DB row per color variant.

    Preference order:
    1. Available variant with image
    2. Available variant
    3. Any variant with image
    4. First variant
    """
    for variant in variants:
        if get_variant_available(variant) and variant.get("featured_image"):
            return variant

    for variant in variants:
        if get_variant_available(variant):
            return variant

    for variant in variants:
        if variant.get("featured_image"):
            return variant

    return variants[0]


def group_variants_by_color(product_json):
    variants = product_json.get("variants", [])
    color_option_index = get_color_option_index(product_json)

    grouped_variants = {}

    for variant in variants:
        color_value = get_variant_option_value(variant, color_option_index)

        if not color_value:
            color_value = "unknown"

        color_key = clean_text(color_value).lower()

        grouped_variants.setdefault(color_key, []).append(variant)

    return grouped_variants


def extract_products_from_shopify_json(product_json, product_url):
    title = clean_title(product_json.get("title")) or title_from_url(product_url)
    description = (
        clean_product_description(product_json.get("description"))
        or clean_product_description(product_json.get("body_html"))
        or f"Kelly Felder dress: {title}"
    )

    grouped_variants = group_variants_by_color(product_json)
    crawled_products = []

    for color_key, variants in grouped_variants.items():
        selected_variant = get_best_variant_for_color(variants)
        raw_color_value = get_variant_option_value(
            selected_variant,
            get_color_option_index(product_json),
        )

        if not raw_color_value:
            raw_color_value = color_key

        normalized_colors = normalize_variant_color(raw_color_value)
        image_url = get_variant_image_url(selected_variant, product_json)
        availability = any(get_variant_available(variant) for variant in variants)
        variant_product_url = get_variant_product_url(product_url, selected_variant)
        price = parse_shopify_variant_price(selected_variant.get("price"))

        crawled_products.append(
            {
                "item_id": create_item_id(product_url, variant_color=raw_color_value),
                "title": title,
                "category": "dress",
                "subcategory": "dress",
                "color": normalized_colors,
                "style": infer_styles_from_text(title, description),
                "brand": "Kelly Felder",
                "price": price,
                "currency": "LKR",
                "image_url": image_url,
                "product_url": variant_product_url,
                "source": "kelly_felder",
                "description": description,
                "availability": availability,
            }
        )

    return crawled_products


def extract_image_from_srcset(srcset):
    image_urls = []

    for srcset_item in srcset.split(","):
        image_url = clean_text(srcset_item).split(" ")[0]
        if image_url:
            image_urls.append(image_url)

    if not image_urls:
        return None

    return image_urls[-1]


def is_valid_product_image_url(image_url):
    if not image_url:
        return False

    image_url_lower = image_url.lower()

    if image_url_lower.startswith("data:"):
        return False

    blocked_words = ["logo", "icon", "placeholder", "spinner", "loading"]
    if any(word in image_url_lower for word in blocked_words):
        return False

    image_path = image_url_lower.split("?")[0]
    image_extensions = (".jpg", ".jpeg", ".png", ".webp", ".avif")

    return image_path.endswith(image_extensions)


def image_url_from_tag(image_tag, page_url):
    for attr in ["srcset", "data-srcset"]:
        if image_tag.get(attr):
            image_url = extract_image_from_srcset(image_tag[attr])

            if image_url:
                absolute_url = make_absolute_url(image_url, page_url)

                if is_valid_product_image_url(absolute_url):
                    return upgrade_shopify_image_quality(absolute_url)

    for attr in ["src", "data-src", "data-image", "data-original", "data-zoom"]:
        if image_tag.get(attr):
            absolute_url = make_absolute_url(image_tag[attr], page_url)

            if is_valid_product_image_url(absolute_url):
                return upgrade_shopify_image_quality(absolute_url)

    return None


def extract_fallback_html_product(product_url):
    """
    Fallback only.
    Main logic uses Shopify JSON because it gives variant-level availability.
    """
    response = requests.get(
        product_url,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = clean_text(soup.get_text(" ", strip=True))

    heading = soup.find("h1")
    title = clean_title(heading.get_text(" ", strip=True)) if heading else title_from_url(product_url)

    meta_description = soup.find("meta", attrs={"name": "description"})
    description = None

    if meta_description and meta_description.get("content"):
        description = clean_product_description(meta_description["content"])

    description = description or f"Kelly Felder dress: {title}"

    image_url = None

    for selector in [{"property": "og:image"}, {"name": "twitter:image"}]:
        meta_image = soup.find("meta", attrs=selector)

        if meta_image and meta_image.get("content"):
            candidate = make_absolute_url(meta_image["content"], product_url)

            if is_valid_product_image_url(candidate):
                image_url = upgrade_shopify_image_quality(candidate)
                break

    if not image_url:
        for image_tag in soup.find_all("img"):
            image_url = image_url_from_tag(image_tag, product_url)

            if image_url:
                break

    price = extract_price(page_text)
    colors = infer_color_from_text(title, description)
    availability = "add to cart" in page_text.lower() and "sold out" not in page_text.lower()

    return [
        {
            "item_id": create_item_id(product_url),
            "title": title,
            "category": "dress",
            "subcategory": "dress",
            "color": colors,
            "style": infer_styles_from_text(title, description),
            "brand": "Kelly Felder",
            "price": price,
            "currency": "LKR",
            "image_url": image_url or KELLY_FELDER_PLACEHOLDER_IMAGE_URL,
            "product_url": product_url,
            "source": "kelly_felder",
            "description": description,
            "availability": availability,
        }
    ]


def extract_collection_title(link_text, product_url):
    title = clean_title(link_text)
    return title or title_from_url(product_url)


def crawl_single_kelly_felder_product(product_url):
    try:
        product_json = fetch_product_json(product_url)
        return extract_products_from_shopify_json(product_json, product_url)
    except Exception:
        return extract_fallback_html_product(product_url)


def crawl_kelly_felder_dresses(max_items=10):
    response = requests.get(
        KELLY_FELDER_DRESSES_URL,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    product_urls = []
    seen_urls = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if "/products/" not in href:
            continue

        product_url = clean_product_url(href)

        if not product_url:
            continue

        if product_url in seen_urls:
            continue

        seen_urls.add(product_url)
        product_urls.append(product_url)

    crawled_products = []

    for product_url in product_urls:
        product_variants = crawl_single_kelly_felder_product(product_url)
        crawled_products.extend(product_variants)

        if len(crawled_products) >= max_items:
            break

    return crawled_products[:max_items]
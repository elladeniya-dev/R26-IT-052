import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


CHENARA_BASE_URL = "https://www.chenaradodge.lk"
CHENARA_PLACEHOLDER_IMAGE_URL = "https://example.com/chenara-dodge-placeholder.jpg"

CHENARA_COLLECTIONS = [
    {
        "name": "tops",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/TOPS",
        "category": "top",
        "subcategory": "top",
        "extra_styles": ["casual", "smart_casual"],
    },
    {
        "name": "pants",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/PANTS",
        "category": "pants",
        "subcategory": "pants",
        "extra_styles": ["casual"],
    },
    {
        "name": "skirts",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/SKIRTS",
        "category": "skirt",
        "subcategory": "skirt",
        "extra_styles": ["casual"],
    },
    {
        "name": "mini_dresses",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/MINI-DRESSES",
        "category": "dress",
        "subcategory": "mini_dress",
        "extra_styles": ["party", "mini"],
    },
    {
        "name": "rompers",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/ROMPERS",
        "category": "jumpsuit",
        "subcategory": "romper",
        "extra_styles": ["casual", "summer"],
    },
    {
        "name": "midi_dresses",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/MIDI-DRESSES",
        "category": "dress",
        "subcategory": "midi_dress",
        "extra_styles": ["casual", "midi"],
    },
    {
        "name": "maxi_dresses",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/MAXI-DRESSES",
        "category": "dress",
        "subcategory": "maxi_dress",
        "extra_styles": ["casual", "maxi", "elegant"],
    },
    {
        "name": "shorts",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/SHORTS",
        "category": "shorts",
        "subcategory": "shorts",
        "extra_styles": ["casual", "summer"],
    },
    {
        "name": "jumpsuits",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/JUMPSUITS",
        "category": "jumpsuit",
        "subcategory": "jumpsuit",
        "extra_styles": ["casual"],
    },
    {
        "name": "two_piece_sets",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/TWO-PIECE-SETS",
        "category": "set",
        "subcategory": "two_piece_set",
        "extra_styles": ["casual", "trendy"],
    },
    {
        "name": "kurtas",
        "url": "https://www.chenaradodge.lk/shop/SHOP-NOW/KURTAS",
        "category": "top",
        "subcategory": "kurta",
        "extra_styles": ["casual", "ethnic", "elegant"],
    },
]


COLOR_ALIASES = {
    "black": ["black", "jet black"],
    "white": ["white", "off white", "ivory"],
    "red": ["red", "maroon", "burgundy", "wine"],
    "blue": ["blue", "navy", "navy blue", "dark blue", "light blue", "denim"],
    "green": ["green", "olive", "sage", "mint", "khaki green"],
    "pink": ["pink", "baby pink", "rose", "blush"],
    "beige": ["beige", "cream", "nude", "sand", "khaki", "natural"],
    "grey": ["grey", "gray", "light gray", "light grey", "charcoal", "silver"],
    "brown": ["brown", "mocha", "coffee", "chocolate", "tan"],
    "yellow": ["yellow", "butter yellow", "mustard"],
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
    ("dress", "mini_dress", ["mini dress"]),
    ("dress", "midi_dress", ["midi dress"]),
    ("dress", "maxi_dress", ["maxi dress", "kaftan"]),
    ("dress", "dress", ["dress"]),
    ("top", "shirt", ["shirt"]),
    ("top", "blazer", ["blazer", "jacket"]),
    ("top", "tshirt", ["tshirt", "t-shirt", "tee"]),
    ("top", "crop_top", ["crop top", "cropped top"]),
    ("top", "kurta", ["kurta"]),
    ("top", "top", ["top", "blouse", "bustier", "halter"]),
    ("pants", "pants", ["pant", "pants", "trouser", "trousers"]),
    ("jeans", "jeans", ["jean", "jeans", "denim"]),
    ("jumpsuit", "romper", ["romper", "rompers"]),
    ("jumpsuit", "jumpsuit", ["jumpsuit"]),
    ("skirt", "skirt", ["skirt", "skort"]),
    ("shorts", "shorts", ["short", "shorts"]),
    ("set", "two_piece_set", ["two piece", "two-piece", "co ord", "co-ord", "set"]),
]


STYLE_KEYWORDS = {
    "formal": ["formal", "office", "workwear", "work wear", "blazer", "button down", "collar", "tailored"],
    "smart_casual": ["shirt", "collar", "button down", "blazer", "pintuck"],
    "casual": ["casual", "everyday", "daily", "relaxed"],
    "party": ["party", "evening", "cocktail", "occasion", "lace", "bustier"],
    "elegant": ["elegant", "lace", "pleated", "satin", "kaftan"],
    "minimal": ["minimal", "basic", "plain", "solid", "classic", "clean"],
    "trendy": ["trendy", "new", "new arrival", "fashion", "tie up", "front tie"],
    "summer": ["summer", "sleeveless", "halter", "strap"],
    "floral": ["floral", "flower", "printed", "print"],
    "denim": ["denim", "jeans"],
    "fitted": ["bodycon", "fitted", "slim", "stretch", "bustier"],
    "relaxed": ["relaxed", "oversized", "loose"],
    "maxi": ["maxi"],
    "midi": ["midi"],
    "mini": ["mini"],
    "ethnic": ["kurta"],
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


def slugify(value):
    value = clean_text(value).lower()
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value)
    return value.strip("_") or "unknown"


def make_absolute_url(url, page_url=CHENARA_BASE_URL):
    url = clean_text(url)

    if not url:
        return None

    if url.startswith("//"):
        return f"https:{url}"

    return urljoin(page_url, url)


def clean_product_url(product_url):
    absolute_url = make_absolute_url(product_url, CHENARA_BASE_URL)

    if not absolute_url:
        return None

    parsed_url = urlparse(absolute_url)

    if "/item/" not in parsed_url.path:
        return None

    return urlunparse(
        (
            "https",
            "www.chenaradodge.lk",
            parsed_url.path,
            "",
            "",
            "",
        )
    )


def get_product_slug(product_url):
    path_parts = [part for part in urlparse(product_url).path.split("/") if part]

    if len(path_parts) >= 2:
        return path_parts[-2]

    return path_parts[-1] if path_parts else "product"


def get_product_id(product_url):
    path_parts = [part for part in urlparse(product_url).path.split("/") if part]

    if path_parts and path_parts[-1].isdigit():
        return path_parts[-1]

    return slugify(product_url)


def add_page_number(collection_url, page_number):
    if page_number <= 1:
        return collection_url

    parsed_url = urlparse(collection_url)
    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
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


def parse_price_from_text(text):
    if not text:
        return None

    matches = re.findall(
        r"(?:LKR|Rs\.?|Rs)\s*([\d,]+(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE,
    )

    if not matches:
        return None

    try:
        return float(matches[0].replace(",", ""))
    except ValueError:
        return None


def normalize_color_value(color_text):
    if not color_text:
        return None

    color_text = clean_text(color_text).lower()
    color_text = re.sub(r"[^a-z\s/&()-]", " ", color_text)
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


def clean_title(title):
    title = remove_emojis(clean_text(title))
    title = re.sub(
        r"\b(new|quick add|out of stock|in stock|sale|off)\b",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.split(
        r"(?:LKR|Rs\.?|Rs)\s*[\d,]+(?:\.\d{1,2})?",
        title,
        flags=re.IGNORECASE,
    )[0]

    return clean_text(title)


def infer_category_from_text(text, fallback_category, fallback_subcategory):
    searchable_text = clean_text(text).lower()

    for category, subcategory, keywords in CATEGORY_KEYWORDS:
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", searchable_text):
                return category, subcategory

    return fallback_category, fallback_subcategory


def infer_styles_from_text(title, description, extra_styles=None):
    extra_styles = extra_styles or []
    searchable_text = f"{title or ''} {description or ''}".lower()

    styles = ["casual"]

    for style, keywords in STYLE_KEYWORDS.items():
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", searchable_text, flags=re.IGNORECASE):
                styles.append(style)
                break

    styles.extend(extra_styles)

    return list(dict.fromkeys([style for style in styles if style]))


def extract_title_from_detail_page(soup, fallback_title):
    title_tag = soup.find("h1")

    if title_tag:
        title = clean_title(title_tag.get_text(" ", strip=True))
        if title:
            return title

    meta_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "title"})

    if meta_title and meta_title.get("content"):
        title = clean_title(meta_title.get("content"))
        if title:
            return title

    return clean_title(fallback_title)


def extract_image_from_detail_page(soup, title=""):
    meta_image = soup.find("meta", property="og:image")

    if meta_image and meta_image.get("content"):
        return make_absolute_url(meta_image.get("content"), CHENARA_BASE_URL)

    image_candidates = []

    for image in soup.find_all("img"):
        image_url = (
            image.get("src")
            or image.get("data-src")
            or image.get("data-original")
            or image.get("data-lazy")
        )

        image_url = make_absolute_url(image_url, CHENARA_BASE_URL)

        if not image_url:
            continue

        alt_text = clean_text(image.get("alt", ""))
        score = 0

        if "greencloudpos.com/chenaradodge.lk/product" in image_url:
            score += 5

        if title and title.lower() in alt_text.lower():
            score += 3

        if "logo" in image_url.lower() or "koko" in image_url.lower() or "mint" in image_url.lower():
            score -= 5

        image_candidates.append((score, image_url))

    if image_candidates:
        image_candidates.sort(key=lambda item: item[0], reverse=True)
        return image_candidates[0][1]

    return CHENARA_PLACEHOLDER_IMAGE_URL


def extract_color_text_from_detail_text(page_text):
    patterns = [
        r"\d+\s*Color\(s\)\s*:\s*(.*?)(?:\d+\s*Size\(s\)|Availability\s*:|Brand\s*:|Code\s*:|Product Information)",
        r"Color\(s\)\s*:\s*(.*?)(?:Size\(s\)|Availability\s*:|Brand\s*:|Code\s*:|Product Information)",
    ]

    for pattern in patterns:
        match = re.search(pattern, page_text, flags=re.IGNORECASE | re.DOTALL)

        if match:
            color_text = clean_text(match.group(1))
            color_text = re.sub(r"\bImage:\b", " ", color_text, flags=re.IGNORECASE)
            return clean_text(color_text)

    return ""


def extract_availability_from_text(page_text):
    normalized_text = clean_text(page_text).lower()

    if "availability : out of stock" in normalized_text:
        return False

    if "out of stock" in normalized_text:
        return False

    return True


def extract_description_from_detail_text(page_text, title, category_config):
    text = clean_text(page_text)

    product_info_match = re.search(
        r"Product Information\s*(.*?)(?:Size Guide|Delivery Information|Customer Reviews|Write a review|Copyright)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if product_info_match:
        description = clean_text(product_info_match.group(1))
        if description:
            return description[:700]

    return (
        f"Chenara Dodge fashion product: {title}. "
        f"Collection: {category_config['name'].replace('_', ' ')}."
    )


def create_item_id(product_url, color_value=None):
    product_id = get_product_id(product_url)
    slug = slugify(get_product_slug(product_url))

    if color_value and color_value != "unknown":
        return f"CHENARA_DODGE_{slug}_{product_id}_{slugify(color_value)}"

    return f"CHENARA_DODGE_{slug}_{product_id}"


def extract_product_links_from_collection(collection_url, max_items):
    product_urls = []
    seen_urls = set()

    for page_number in range(1, 4):
        page_url = add_page_number(collection_url, page_number)

        try:
            response = SESSION.get(page_url, timeout=20)
            response.raise_for_status()
        except Exception as error:
            print(f"Chenara Dodge collection failed: {page_url} - {error}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        page_product_urls = []

        for link in soup.find_all("a", href=True):
            product_url = clean_product_url(link["href"])

            if not product_url:
                continue

            if product_url in seen_urls:
                continue

            seen_urls.add(product_url)
            page_product_urls.append(product_url)
            product_urls.append(product_url)

            if len(product_urls) >= max_items:
                return product_urls

        if not page_product_urls:
            break

    return product_urls


def extract_product_from_detail_page(product_url, category_config):
    response = SESSION.get(product_url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text(" ", strip=True)

    fallback_title = get_product_slug(product_url).replace("-", " ")
    title = extract_title_from_detail_page(soup, fallback_title)

    availability = extract_availability_from_text(page_text)

    if not availability:
        return None

    color_text = extract_color_text_from_detail_text(page_text)
    colors = normalize_colors_from_text(color_text)

    if not colors:
        colors = normalize_colors_from_text(f"{title} {page_text}")

    if not colors:
        colors = ["unknown"]

    price = parse_price_from_text(page_text)
    image_url = extract_image_from_detail_page(soup, title)
    description = extract_description_from_detail_text(page_text, title, category_config)

    category, subcategory = infer_category_from_text(
        text=f"{title} {description}",
        fallback_category=category_config["category"],
        fallback_subcategory=category_config["subcategory"],
    )

    return {
        "item_id": create_item_id(product_url, colors[0]),
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "color": colors,
        "style": infer_styles_from_text(
            title=title,
            description=description,
            extra_styles=category_config.get("extra_styles", []),
        ),
        "brand": "Chenara Dodge",
        "price": price,
        "currency": "LKR",
        "image_url": image_url,
        "product_url": product_url,
        "source": "chenara_dodge",
        "description": description,
        "availability": True,
    }


def crawl_single_chenara_dodge_product(product_url, category_config):
    try:
        return extract_product_from_detail_page(
            product_url=product_url,
            category_config=category_config,
        )
    except Exception as error:
        print(f"Chenara Dodge product failed: {product_url} - {error}")
        return None


def deduplicate_products(products):
    unique_products = []
    seen_item_ids = set()

    for product in products:
        if not product:
            continue

        item_id = product.get("item_id")

        if not item_id or item_id in seen_item_ids:
            continue

        seen_item_ids.add(item_id)
        unique_products.append(product)

    return unique_products


def crawl_chenara_dodge_products(max_items=10):
    """
    Crawls Chenara Dodge collection pages and product detail pages.

    Important:
    - This website is not Shopify-style.
    - max_items means max product URLs per collection.
    - Product detail pages are checked for out-of-stock text.
    - Only available products are returned.
    """

    max_items = max_items or 10
    all_products = []
    seen_product_urls = set()

    for collection_config in CHENARA_COLLECTIONS:
        product_urls = extract_product_links_from_collection(
            collection_url=collection_config["url"],
            max_items=max_items,
        )

        for product_url in product_urls:
            if product_url in seen_product_urls:
                continue

            seen_product_urls.add(product_url)

            product = crawl_single_chenara_dodge_product(
                product_url=product_url,
                category_config=collection_config,
            )

            if product:
                all_products.append(product)

    unique_products = deduplicate_products(all_products)
    print(f"Chenara Dodge crawler success: {len(unique_products)} available products")

    return unique_products


def crawl_chenara_dodge_all_clothing(max_items=10):
    return crawl_chenara_dodge_products(max_items=max_items)
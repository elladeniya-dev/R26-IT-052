import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


CARNAGE_CROP_TOPS_URL = "https://incarnage.com/collections/womens-crop-tops"
CARNAGE_PLACEHOLDER_IMAGE_URL = "https://example.com/carnage-placeholder.jpg"


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def clean_product_description(description):
    if not description:
        return None

    description = clean_text(description)

    # Fix broken page-text prefixes such as "78This crop top..."
    description = re.sub(r"^\d+(?=[A-Za-z])", "", description)

    description = re.sub(
        r"^(?:Product\s+details:?\s*)+",
        "",
        description,
        flags=re.IGNORECASE
    )
    description = re.sub(
        r"(?:\s*Product\s+details:?\s*)+$",
        "",
        description,
        flags=re.IGNORECASE
    )

    description = clean_text(description).strip(" -:|")

    return description or None


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


def infer_styles_from_text(title, description):
    searchable_text = f"{title or ''} {description or ''}".lower()
    styles = ["casual"]

    style_keywords = {
        "activewear": [
            "training",
            "gym",
            "workout",
            "moisture-wicking",
            "moisture wicking",
            "sweat-wicking",
            "sweat wicking"
        ],
        "athleisure": ["athleisure"],
        "lifestyle": ["lifestyle", "everyday", "daily wear"],
        "seamless": ["seamless"],
        "ribbed": ["ribbed"],
        "fitted": ["sleek", "sculpted", "body-hugging", "body hugging"],
        "smart_casual": ["polo", "collar"]
    }

    for style, keywords in style_keywords.items():
        for keyword in keywords:
            if keyword in searchable_text:
                styles.append(style)
                break

    return styles


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


def extract_detail_page_title(soup):
    title_candidates = []

    heading = soup.find("h1")
    if heading:
        title_candidates.append(heading.get_text(" ", strip=True))

    for selector in [
        {"property": "og:title"},
        {"name": "twitter:title"},
    ]:
        meta_title = soup.find("meta", attrs=selector)
        if meta_title and meta_title.get("content"):
            title_candidates.append(meta_title["content"])

    if soup.title and soup.title.string:
        title_candidates.append(soup.title.string)

    for candidate in title_candidates:
        title = remove_emojis(clean_text(candidate))
        title = re.sub(
            r"\s*(?:\||–|-)\s*CARNAGE.*$",
            "",
            title,
            flags=re.IGNORECASE
        )
        title = clean_text(title)

        if title:
            return title

    return None


def make_absolute_image_url(image_url, product_url):
    image_url = clean_text(image_url)

    if image_url.startswith("//"):
        return f"https:{image_url}"

    return urljoin(product_url, image_url)


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


def image_url_from_tag(image_tag, product_url):
    for attr in ["srcset", "data-srcset"]:
        if image_tag.get(attr):
            image_url = extract_image_from_srcset(image_tag[attr])
            if image_url:
                absolute_url = make_absolute_image_url(image_url, product_url)
                if is_valid_product_image_url(absolute_url):
                    return absolute_url

    for attr in ["src", "data-src", "data-image", "data-original", "data-zoom"]:
        if image_tag.get(attr):
            absolute_url = make_absolute_image_url(image_tag[attr], product_url)
            if is_valid_product_image_url(absolute_url):
                return absolute_url

    return None


def extract_detail_page_image(soup, product_url):
    for selector in [
        {"property": "og:image"},
        {"name": "twitter:image"},
    ]:
        meta_image = soup.find("meta", attrs=selector)
        if meta_image and meta_image.get("content"):
            image_url = make_absolute_image_url(meta_image["content"], product_url)
            if is_valid_product_image_url(image_url):
                return image_url

    product_image_keywords = re.compile(
        r"product|featured|main|gallery|media",
        flags=re.IGNORECASE
    )

    for image_tag in soup.find_all("img"):
        searchable_text = " ".join([
            image_tag.get("class") and " ".join(image_tag.get("class")) or "",
            image_tag.get("id", ""),
            image_tag.get("alt", "")
        ])

        if not product_image_keywords.search(searchable_text):
            continue

        image_url = image_url_from_tag(image_tag, product_url)
        if image_url:
            return image_url

    for image_tag in soup.find_all("img"):
        image_url = image_url_from_tag(image_tag, product_url)
        if image_url:
            return image_url

    return None


def extract_product_detail_data(product_url):
    """
    Opens a Carnage product detail page and extracts more accurate product data.
    This improves collection-page crawling by getting exact title, image,
    color, and description.
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
        detail_title = extract_detail_page_title(soup)
        detail_image_url = extract_detail_page_image(soup, product_url)

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
            description = clean_product_description(description_match.group(1))

        # Check availability
        is_sold_out = "sold out" in page_text.lower()

        return {
            "title": detail_title,
            "image_url": detail_image_url,
            "color_text": extracted_color_text,
            "description": description,
            "availability": not is_sold_out
        }

    except Exception:
        return {
            "title": None,
            "image_url": None,
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

        trusted_title = detail_data["title"] or item["title"]
        image_url = detail_data["image_url"] or CARNAGE_PLACEHOLDER_IMAGE_URL
        color_source_text = detail_data["color_text"] or trusted_title
        description = detail_data["description"] or f"Carnage women's crop top: {trusted_title}"
        styles = infer_styles_from_text(trusted_title, description)

        crawled_products.append({
            "item_id": create_item_id(item["product_url"]),
            "title": trusted_title,
            "category": "top",
            "subcategory": "crop_top",
            "color": infer_color_from_title(color_source_text),
            "style": styles,
            "brand": "Carnage",
            "price": item["price"],
            "currency": "LKR",
            "image_url": image_url,
            "product_url": item["product_url"],
            "source": "carnage",
            "description": description,
            "availability": item["availability"] and detail_data["availability"]
        })

    return crawled_products

import json
import re
from html import unescape
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


GFLOCK_DRESSES_URL = "https://gflock.lk/collections/dresses?sort_by=created-descending&filter.v.availability=1"
GFLOCK_PLACEHOLDER_IMAGE_URL = "https://example.com/gflock-placeholder.jpg"


def clean_text(text):
    return re.sub(r"\s+", " ", unescape(str(text or ""))).strip()


def clean_product_description(description):
    if not description:
        return None

    description = clean_text(description)
    description = re.sub(
        r"^(?:Description|Product\s+details?):?\s*",
        "",
        description,
        flags=re.IGNORECASE
    )
    description = re.sub(
        r"\s*(?:Description|Product\s+details?):?\s*$",
        "",
        description,
        flags=re.IGNORECASE
    )
    description = clean_text(description).strip(" -:|")

    return description or None


def extract_reliable_availability(soup, json_ld_product):
    structured_availability = extract_structured_availability(json_ld_product)
    if structured_availability is not None:
        return structured_availability

    return extract_disabled_sold_out_button_availability(soup)


def extract_structured_availability(json_ld_product):
    if not json_ld_product:
        return None

    product_available = json_ld_product.get("available")
    if isinstance(product_available, bool):
        return product_available

    offers = json_ld_product.get("offers") if json_ld_product else None

    if isinstance(offers, list):
        offer_values = []

        for offer in offers:
            if isinstance(offer, dict) and isinstance(offer.get("available"), bool):
                offer_values.append(offer["available"])

        if offer_values and all(value is False for value in offer_values):
            return False
        if offer_values and any(value is True for value in offer_values):
            return True

        return None

    if isinstance(offers, dict) and isinstance(offers.get("available"), bool):
        return offers["available"]

    return None


def extract_disabled_sold_out_button_availability(soup):
    sold_out_text = re.compile(r"sold\s*out|out\s*of\s*stock|unavailable", re.IGNORECASE)

    for form in soup.find_all("form"):
        form_text = " ".join([
            form.get("action", ""),
            form.get("id", ""),
            " ".join(form.get("class", []))
        ]).lower()

        if "cart" not in form_text and "product" not in form_text:
            continue

        for button in form.find_all(["button", "input"]):
            if not button.has_attr("disabled"):
                continue

            button_text = clean_text(
                button.get_text(" ", strip=True) or button.get("value") or ""
            )

            if sold_out_text.search(button_text):
                return False

    return None


def remove_emojis(text):
    return re.sub(
        r"[^\w\s.,/&'()-]",
        "",
        text or ""
    ).strip()


def create_item_id(product_url):
    slug = urlparse(product_url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", slug).strip("_").lower()
    return f"GFLOCK_{slug}"


def title_from_url(product_url):
    slug = urlparse(product_url).path.rstrip("/").split("/")[-1]
    return clean_text(slug.replace("-", " ").replace("_", " ")).title()


def parse_price_value(price_text):
    if price_text is None:
        return None

    price_text = str(price_text).replace(",", "")

    try:
        return float(price_text)
    except ValueError:
        return None


def extract_price(text):
    text = text or ""
    price_patterns = [
        r"(?:LKR|Rs\.?|Rs)\s*([\d,]+(?:\.\d{1,2})?)",
        r"Regular price\s*([\d,]+(?:\.\d{1,2})?)",
        r"Sale price\s*([\d,]+(?:\.\d{1,2})?)"
    ]

    for pattern in price_patterns:
        price_match = re.search(pattern, text, flags=re.IGNORECASE)
        if price_match:
            return parse_price_value(price_match.group(1))

    return None


def clean_title(title):
    title = remove_emojis(clean_text(title))
    title = re.sub(
        r"\s*(?:\||-|–)\s*Gflock.*$",
        "",
        title,
        flags=re.IGNORECASE
    )
    title = re.split(
        r"(?:LKR|Rs\.?|Rs)\s*[\d,]+(?:\.\d{1,2})?",
        title,
        flags=re.IGNORECASE
    )[0]
    title = re.split(
        r"(?:Regular price|Sale price)\s*[\d,]+(?:\.\d{1,2})?",
        title,
        flags=re.IGNORECASE
    )[0]
    title = re.sub(
        r"\b(sold out|sale|new|quick view)\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    return clean_text(title)


def infer_color_from_text(title, description):
    searchable_text = f"{title or ''} {description or ''}".lower()

    color_keywords = {
        "black": ["black"],
        "white": ["white", "ivory"],
        "brown": ["brown", "chocolate", "mocha"],
        "grey": ["grey", "gray"],
        "green": ["green", "sage", "olive"],
        "blue": ["blue", "navy"],
        "red": ["red", "maroon", "burgundy"],
        "pink": ["pink", "rose"],
        "beige": ["beige", "cream", "nude"],
        "purple": ["purple", "lilac", "lavender"],
        "yellow": ["yellow", "mustard"],
        "orange": ["orange"],
        "multi": ["print", "printed", "floral", "stripe", "multi"]
    }

    matched_colors = []

    for color, keywords in color_keywords.items():
        for keyword in keywords:
            if keyword in searchable_text:
                matched_colors.append(color)
                break

    return matched_colors if matched_colors else ["unknown"]


def infer_styles_from_text(title, description):
    searchable_text = f"{title or ''} {description or ''}".lower()
    styles = ["casual"]

    style_keywords = {
        "formal": ["formal", "office", "workwear"],
        "party": ["party", "evening", "cocktail", "occasion"],
        "summer": ["summer", "linen", "sleeveless"],
        "floral": ["floral", "flower", "print", "printed"],
        "fitted": ["fitted", "bodycon", "slim", "sculpted"],
        "relaxed": ["relaxed", "flowy", "loose"],
        "smart_casual": ["shirt dress", "collar", "button"],
        "maxi": ["maxi"],
        "midi": ["midi"],
        "mini": ["mini"]
    }

    for style, keywords in style_keywords.items():
        for keyword in keywords:
            if keyword in searchable_text:
                styles.append(style)
                break

    return styles


def make_absolute_url(url, page_url):
    url = clean_text(url)

    if url.startswith("//"):
        return f"https:{url}"

    return urljoin(page_url, url)


def clean_product_url(product_url):
    absolute_url = make_absolute_url(product_url, GFLOCK_DRESSES_URL)
    parsed_url = urlparse(absolute_url)
    path_parts = [part for part in parsed_url.path.split("/") if part]

    if "products" in path_parts:
        product_index = path_parts.index("products")
        path_parts = path_parts[:product_index + 2]

    clean_path = "/" + "/".join(path_parts)

    return urlunparse((
        "https",
        "gflock.lk",
        clean_path,
        "",
        "",
        ""
    ))


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
                    return absolute_url

    for attr in ["src", "data-src", "data-image", "data-original", "data-zoom"]:
        if image_tag.get(attr):
            absolute_url = make_absolute_url(image_tag[attr], page_url)
            if is_valid_product_image_url(absolute_url):
                return absolute_url

    return None


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
        title = clean_title(candidate)
        if title:
            return title

    return None


def extract_detail_page_image(soup, product_url):
    for selector in [
        {"property": "og:image"},
        {"name": "twitter:image"},
    ]:
        meta_image = soup.find("meta", attrs=selector)
        if meta_image and meta_image.get("content"):
            image_url = make_absolute_url(meta_image["content"], product_url)
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


def extract_json_ld_product_data(soup):
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        script_text = script.string or script.get_text()
        if not script_text:
            continue

        try:
            data = json.loads(script_text)
        except json.JSONDecodeError:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue

            graph_items = item.get("@graph")
            if isinstance(graph_items, list):
                items.extend(graph_items)
                continue

            item_type = item.get("@type")
            if isinstance(item_type, list):
                is_product = "Product" in item_type
            else:
                is_product = item_type == "Product"

            if is_product:
                return item

    return {}


def extract_detail_page_description(soup):
    meta_description = soup.find("meta", attrs={"name": "description"})
    if meta_description and meta_description.get("content"):
        description = clean_product_description(meta_description["content"])
        if description:
            return description

    page_text = clean_text(soup.get_text(" ", strip=True))
    description_match = re.search(
        r"(?:Description|Product details)\s+(.*?)(?:Size guide|Shipping|Returns|You may also like|Related products)",
        page_text,
        flags=re.IGNORECASE
    )

    if description_match:
        return clean_product_description(description_match.group(1))

    return None


def extract_product_detail_data(product_url):
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
        json_ld_product = extract_json_ld_product_data(soup)

        title = extract_detail_page_title(soup)
        image_url = extract_detail_page_image(soup, product_url)
        description = extract_detail_page_description(soup)
        price = extract_price(page_text)

        if json_ld_product:
            title = title or clean_title(json_ld_product.get("name"))
            description = description or clean_product_description(
                json_ld_product.get("description")
            )

            offers = json_ld_product.get("offers")
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            if isinstance(offers, dict):
                price = price or parse_price_value(offers.get("price"))
        reliable_availability = extract_reliable_availability(soup, json_ld_product)

        return {
            "title": title,
            "image_url": image_url,
            "description": description,
            "price": price,
            "availability": reliable_availability
        }

    except Exception:
        return {
            "title": None,
            "image_url": None,
            "description": None,
            "price": None,
            "availability": None
        }


def extract_collection_title(link_text, product_url):
    title = clean_title(link_text)
    return title or title_from_url(product_url)


def crawl_gflock_dresses(max_items=10):
    response = requests.get(
        GFLOCK_DRESSES_URL,
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

        if "/products/" not in href:
            continue

        product_url = clean_product_url(href)
        link_text = clean_text(link.get_text(" ", strip=True))
        title = extract_collection_title(link_text, product_url)
        price = extract_price(link_text)

        product_links.append({
            "title": title,
            "price": price,
            "product_url": product_url,
            "availability": True
        })

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
        price = detail_data["price"] if detail_data["price"] is not None else item["price"]
        image_url = detail_data["image_url"] or GFLOCK_PLACEHOLDER_IMAGE_URL
        description = detail_data["description"] or f"Gflock dress: {trusted_title}"
        availability = (
            detail_data["availability"]
            if detail_data["availability"] is not None
            else item["availability"]
        )

        crawled_products.append({
            "item_id": create_item_id(item["product_url"]),
            "title": trusted_title,
            "category": "dress",
            "subcategory": "dress",
            "color": infer_color_from_text(trusted_title, description),
            "style": infer_styles_from_text(trusted_title, description),
            "brand": "Gflock",
            "price": price,
            "currency": "LKR",
            "image_url": image_url,
            "product_url": item["product_url"],
            "source": "gflock",
            "description": description,
            "availability": availability
        })

    return crawled_products

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from services.trend_mapping_service import map_products_to_trend_observations


OUTPUT_DIR = Path("output")


PUBLIC_FASHION_SOURCES = [
    {
        "source_name": "Zigzag New Arrivals",
        "source_type": "fashion_website",
        "url": "https://zigzag.lk/collections/new-arrivals-1",
        "product_path_keywords": ["/products/"],
    },
    {
        "source_name": "Kelly Felder New Arrivals",
        "source_type": "fashion_website",
        "url": "https://kellyfelder.com/collections/new-arrivals",
        "product_path_keywords": ["/products/"],
    },
    {
        "source_name": "Mimosa New Arrivals",
        "source_type": "fashion_website",
        "url": "https://mimosaforever.com/collections/new-arrivals",
        "product_path_keywords": ["/products/"],
    },
]


def fetch_page_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=25,
    )

    response.raise_for_status()
    return response.text


def clean_text(text: str) -> str:
    return " ".join(text.split()).strip()


def remove_query_params(url: str) -> str:
    parsed_url = urlparse(url)

    clean_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        "",
        "",
        "",
    ))

    return clean_url.rstrip("/")


def canonical_product_url(url: str) -> str:
    """
    Convert Shopify collection product URLs into one canonical product URL.

    Example:
    https://kellyfelder.com/collections/new-arrivals/products/the-kinetic-sculpt-bralette
    becomes:
    https://kellyfelder.com/products/the-kinetic-sculpt-bralette
    """
    clean_url = remove_query_params(url)
    parsed_url = urlparse(clean_url)

    path_parts = [
        part for part in parsed_url.path.split("/")
        if part
    ]

    if "products" in path_parts:
        product_index = path_parts.index("products")

        if product_index + 1 < len(path_parts):
            product_slug = path_parts[product_index + 1]
            canonical_path = f"/products/{product_slug}"

            return urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                canonical_path,
                "",
                "",
                "",
            )).rstrip("/")

    return clean_url


def is_product_link(href: str, product_path_keywords: list[str]) -> bool:
    if not href:
        return False

    href_lower = href.lower()

    return any(keyword in href_lower for keyword in product_path_keywords)


def title_from_product_url(product_url: str) -> str:
    path = urlparse(product_url).path
    slug = path.rstrip("/").split("/")[-1]

    if not slug:
        return ""

    words = slug.replace("-", " ").split()
    title = " ".join(word.capitalize() for word in words)

    return clean_title(title)


def clean_title(title: str) -> str:
    title = clean_text(title)

    if not title:
        return ""

    # Remove common unwanted words from copied product slugs/titles.
    title = re.sub(r"\bcopy\b", "", title, flags=re.IGNORECASE)

    # Remove Mimosa-style product code suffixes.
    # Examples:
    # Mpc8pc8997 1
    # Mft1tc10238 1
    # R0406a2400 1
    # Mdr3dc3998 1
    title = re.sub(
        r"\b[A-Za-z]{1,5}\d{1,6}[A-Za-z]{0,4}\d{0,6}\s*\d*\b$",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\bR\d{4}[A-Za-z]\d{4}\s*\d*\b$",
        "",
        title,
        flags=re.IGNORECASE
    )

    # Remove trailing standalone numbers added from product variants/slugs.
    title = re.sub(r"\s+\d+$", "", title)

    # Fix spacing around hyphenated words after title conversion.
    title = title.replace(" - ", "-")
    title = title.replace("- ", "-")
    title = title.replace(" -", "-")

    # Common spelling cleanup from source slugs.
    title = title.replace("Sleeveed", "Sleeved")
    title = title.replace("Baloon", "Balloon")
    title = title.replace("Tassle", "Tassel")
    title = title.replace("Nck", "Neck")
    title = title.replace("Slirt", "Skirt")
    title = title.replace("Asymetrical", "Asymmetrical")

    return clean_text(title)


def is_bad_title(title: str) -> bool:
    if not title:
        return True

    title = clean_title(title)
    title_lower = title.lower().strip()

    bad_exact_values = {
        "quick view",
        "add to cart",
        "select options",
        "read more",
        "view cart",
        "checkout",
        "login",
        "register",
        "wishlist",
        "compare",
        "sale",
        "regular price",
        "unit price",
        "tax included",
        "shipping calculated",
        "1 more",
        "2 more",
        "3 more",
        "4 more",
        "5 more",
        "copy",
    }

    if title_lower in bad_exact_values:
        return True

    size_patterns = [
        r"^uk\s*\d{1,2}$",
        r"^uk\s*\d{1,2}\s*-\s*\d{1,2}$",
        r"^age\s*\d+\s*-\s*\d+$",
        r"^age\s*\d+\s*-\s*\d+\s*years?$",
        r"^xs$",
        r"^s$",
        r"^m$",
        r"^l$",
        r"^xl$",
        r"^xxl$",
    ]

    for pattern in size_patterns:
        if re.match(pattern, title_lower):
            return True

    if len(title) < 4:
        return True

    if title.isdigit():
        return True

    return False


def extract_title_from_link(link, product_url: str) -> str:
    visible_title = clean_title(link.get_text(" ", strip=True))

    image = link.find("img")

    image_title = ""
    if image:
        image_title = (
            image.get("alt")
            or image.get("title")
            or ""
        )
        image_title = clean_title(image_title)

    slug_title = title_from_product_url(product_url)

    title_candidates = [
        visible_title,
        image_title,
        slug_title,
    ]

    good_candidates = [
        title for title in title_candidates
        if title and not is_bad_title(title)
    ]

    if good_candidates:
        return max(good_candidates, key=len)

    return slug_title


def looks_like_product_title(title: str) -> bool:
    title = clean_title(title)

    if is_bad_title(title):
        return False

    title_lower = title.lower()

    ignored_phrases = [
        "quick view",
        "add to cart",
        "select options",
        "read more",
        "view cart",
        "checkout",
        "login",
        "register",
        "wishlist",
        "compare",
        "regular price",
        "unit price",
        "tax included",
        "shipping calculated",
    ]

    if any(phrase in title_lower for phrase in ignored_phrases):
        return False

    return True


def title_quality_score(title: str) -> int:
    title = clean_title(title)
    title_lower = title.lower()

    score = len(title)

    useful_words = [
        "dress",
        "top",
        "shirt",
        "skirt",
        "pant",
        "trouser",
        "denim",
        "linen",
        "crop",
        "sleeveless",
        "oversized",
        "printed",
        "stripe",
        "halter",
        "bralette",
        "jumpsuit",
        "cardigan",
        "blazer",
        "short",
    ]

    for word in useful_words:
        if word in title_lower:
            score += 20

    weak_words = [
        "copy",
        "more",
        "uk",
        "age",
    ]

    for word in weak_words:
        if word in title_lower:
            score -= 30

    return score


def is_better_title(new_title: str, old_title: str) -> bool:
    new_title = clean_title(new_title)
    old_title = clean_title(old_title)

    if is_bad_title(old_title) and not is_bad_title(new_title):
        return True

    return title_quality_score(new_title) > title_quality_score(old_title)


def extract_products_from_html(
    html: str,
    base_url: str,
    source_name: str,
    source_type: str,
    product_path_keywords: list[str],
) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    product_map = {}

    product_links = soup.find_all(
        "a",
        href=lambda href: is_product_link(href, product_path_keywords)
    )

    for link in product_links:
        href = link.get("href")

        full_url = urljoin(base_url, href)
        product_url = canonical_product_url(full_url)

        title = extract_title_from_link(
            link=link,
            product_url=product_url,
        )

        title = clean_title(title)

        if not looks_like_product_title(title):
            continue

        if product_url not in product_map:
            product_map[product_url] = {
                "title": title,
                "product_url": product_url,
            }
        else:
            old_title = product_map[product_url]["title"]

            if is_better_title(title, old_title):
                product_map[product_url]["title"] = title

    products = []

    for index, product in enumerate(product_map.values(), start=1):
        products.append({
            "rank_position": index,
            "title": clean_title(product["title"]),
            "product_url": product["product_url"],
            "source_name": source_name,
            "source_type": source_type,
        })

    return products


def save_json(file_path: Path, data) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def make_safe_file_name(source_name: str) -> str:
    return (
        source_name
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def collect_single_source(source: dict) -> dict:
    source_name = source["source_name"]
    source_type = source["source_type"]
    source_url = source["url"]
    product_path_keywords = source["product_path_keywords"]

    print(f"\nCollecting source: {source_name}")
    print(f"URL: {source_url}")

    html = fetch_page_html(source_url)

    products = extract_products_from_html(
        html=html,
        base_url=source_url,
        source_name=source_name,
        source_type=source_type,
        product_path_keywords=product_path_keywords,
    )

    observations = map_products_to_trend_observations(
        products=products,
        source_name=source_name,
        source_type=source_type,
    )

    safe_name = make_safe_file_name(source_name)

    raw_products_file = OUTPUT_DIR / f"{safe_name}_raw_products.json"
    observations_file = OUTPUT_DIR / f"{safe_name}_trend_observations.json"

    save_json(raw_products_file, products)
    save_json(observations_file, observations)

    print(f"Raw products found: {len(products)}")
    print(f"Trend observations created: {len(observations)}")

    return {
        "source_name": source_name,
        "source_url": source_url,
        "raw_product_count": len(products),
        "trend_observation_count": len(observations),
        "raw_products_file": str(raw_products_file),
        "trend_observations_file": str(observations_file),
        "products": products,
        "observations": observations,
    }


def collect_all_public_fashion_sources() -> dict:
    all_products = []
    all_observations = []
    source_results = []

    for source in PUBLIC_FASHION_SOURCES:
        try:
            result = collect_single_source(source)

            source_results.append({
                "source_name": result["source_name"],
                "source_url": result["source_url"],
                "raw_product_count": result["raw_product_count"],
                "trend_observation_count": result["trend_observation_count"],
                "raw_products_file": result["raw_products_file"],
                "trend_observations_file": result["trend_observations_file"],
                "status": "success",
            })

            all_products.extend(result["products"])
            all_observations.extend(result["observations"])

            time.sleep(2)

        except Exception as error:
            print(f"Failed to collect source: {source['source_name']}")
            print(f"Reason: {error}")

            source_results.append({
                "source_name": source["source_name"],
                "source_url": source["url"],
                "raw_product_count": 0,
                "trend_observation_count": 0,
                "status": "failed",
                "error": str(error),
            })

    combined_raw_file = OUTPUT_DIR / "combined_raw_products.json"
    combined_observations_file = OUTPUT_DIR / "combined_trend_observations.json"
    summary_file = OUTPUT_DIR / "collection_summary.json"

    save_json(combined_raw_file, all_products)
    save_json(combined_observations_file, all_observations)

    summary = {
        "total_sources": len(PUBLIC_FASHION_SOURCES),
        "successful_sources": len([
            item for item in source_results
            if item["status"] == "success"
        ]),
        "failed_sources": len([
            item for item in source_results
            if item["status"] == "failed"
        ]),
        "total_raw_products": len(all_products),
        "total_trend_observations": len(all_observations),
        "combined_raw_products_file": str(combined_raw_file),
        "combined_trend_observations_file": str(combined_observations_file),
        "sources": source_results,
    }

    save_json(summary_file, summary)

    return {
        "summary": summary,
        "products": all_products,
        "observations": all_observations,
    }
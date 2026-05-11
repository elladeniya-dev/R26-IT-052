import json
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from services.trend_mapping_service import map_products_to_trend_observations

ZIGZAG_NEW_ARRIVALS_URL = "https://zigzag.lk/collections/new-arrivals-1"

SOURCE_NAME = "Zigzag New Arrivals"
SOURCE_TYPE = "fashion_website"

OUTPUT_DIR = Path("output")
RAW_PRODUCTS_FILE = OUTPUT_DIR / "zigzag_raw_products.json"
TREND_OBSERVATIONS_FILE = OUTPUT_DIR / "zigzag_trend_observations.json"


def fetch_page_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(url, headers=headers, timeout=20)

    response.raise_for_status()
    return response.text


def clean_text(text: str) -> str:
    return " ".join(text.split()).strip()


def extract_product_titles(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    product_map = {}

    product_links = soup.find_all("a", href=lambda href: href and "/products/" in href)

    for link in product_links:
        href = link.get("href")
        product_url = urljoin(base_url, href)

        title = clean_text(link.get_text(" ", strip=True))

        image = link.find("img")
        if not title and image:
            title = image.get("alt") or image.get("title") or ""
            title = clean_text(title)

        if not title:
            continue

        ignored_words = [
            "quick view",
            "add to cart",
            "sold out",
            "sale",
            "regular price",
            "view",
            "login",
        ]

        title_lower = title.lower()

        if (
            any(word in title_lower for word in ignored_words)
            and len(title.split()) <= 3
        ):
            continue

        if product_url not in product_map:
            product_map[product_url] = {"title": title, "product_url": product_url}

    products = []

    for index, product in enumerate(product_map.values(), start=1):
        products.append(
            {
                "rank_position": index,
                "title": product["title"],
                "product_url": product["product_url"],
                "source_name": SOURCE_NAME,
                "source_type": SOURCE_TYPE,
            }
        )

    return products


def save_json(file_path: Path, data) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def collect_zigzag_new_arrivals() -> dict:
    print("Starting public fashion trend data collection...")
    print(f"Source: {ZIGZAG_NEW_ARRIVALS_URL}")

    html = fetch_page_html(ZIGZAG_NEW_ARRIVALS_URL)

    time.sleep(1)

    products = extract_product_titles(html=html, base_url=ZIGZAG_NEW_ARRIVALS_URL)

    observations = map_products_to_trend_observations(
        products=products, source_name=SOURCE_NAME, source_type=SOURCE_TYPE
    )

    save_json(RAW_PRODUCTS_FILE, products)
    save_json(TREND_OBSERVATIONS_FILE, observations)

    return {
        "source_name": SOURCE_NAME,
        "source_url": ZIGZAG_NEW_ARRIVALS_URL,
        "raw_product_count": len(products),
        "trend_observation_count": len(observations),
        "raw_products_file": str(RAW_PRODUCTS_FILE),
        "trend_observations_file": str(TREND_OBSERVATIONS_FILE),
        "observations": observations,
    }

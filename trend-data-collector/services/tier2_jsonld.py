"""
Tier 2: Schema.org JSON-LD Microdata Extraction Engine.
Extracts structured product data embedded in <script type="application/ld+json"> blocks across
category grids or individual sitemap URLs without visual DOM CSS dependencies.
"""
import json
import logging
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

from services.garment_validator import GarmentValidator

logger = logging.getLogger("OutfitIQ.Tier2JsonLD")
MAX_ITEMS_PER_STORE = 100
DEFAULT_TIMEOUT = 8


def execute_tier2_json_ld(store_config: Dict[str, Any], sitemap_urls: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Parse embedded Schema.org JSON-LD microdata from store category grids or discovered sitemap URLs.
    Retrieves accurate names, offers.price, currency, and CDN images independent of CSS changes.
    """
    brand_name = str(store_config.get("brand_name", "Unknown"))
    base_url = str(store_config.get("base_url", "")).rstrip("/")
    segment = str(store_config.get("segment", "General"))

    endpoints = _build_target_web_urls(store_config.get("target_endpoints", []), sitemap_urls)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    validated_items: List[Dict[str, Any]] = []
    seen_urls: Set[str] = set()
    rank = 1

    for ep in endpoints:
        if len(validated_items) >= MAX_ITEMS_PER_STORE:
            break

        target = urljoin(base_url, ep) if not ep.startswith("http") else ep
        try:
            resp = requests.get(target, headers=headers, timeout=DEFAULT_TIMEOUT)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            scripts = soup.find_all("script", type="application/ld+json")

            for sc in scripts:
                content = sc.string or sc.get_text()
                if not content:
                    continue
                try:
                    data = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    continue

                items_list: List[dict] = []
                if isinstance(data, list):
                    items_list = [x for x in data if isinstance(x, dict)]
                elif isinstance(data, dict):
                    if "@graph" in data and isinstance(data["@graph"], list):
                        items_list = [x for x in data["@graph"] if isinstance(x, dict)]
                    elif data.get("@type") in ("Product", "ItemPage") or "itemListElement" in data:
                        items_list = [data]
                    elif isinstance(data.get("mainEntity"), dict) and "itemListElement" in data["mainEntity"]:
                        # Common category-page shape: CollectionPage.mainEntity is
                        # the ItemList (e.g. Kandy Selection, many WooCommerce/SEO themes).
                        items_list = [data["mainEntity"]]

                for entry in items_list:
                    if len(validated_items) >= MAX_ITEMS_PER_STORE:
                        break

                    if "itemListElement" in entry and isinstance(entry["itemListElement"], list):
                        for el in entry["itemListElement"]:
                            if not isinstance(el, dict):
                                continue
                            prod = el.get("item", el)
                            if isinstance(prod, dict) and (prod.get("@type") == "Product" or "name" in prod):
                                _extract_and_add(prod, target, base_url, brand_name, segment, rank, seen_urls, validated_items)
                                rank = len(validated_items) + 1
                    elif entry.get("@type") == "Product":
                        _extract_and_add(entry, target, base_url, brand_name, segment, rank, seen_urls, validated_items)
                        rank = len(validated_items) + 1

        except Exception as err:
            logger.debug(f"[Tier 2] Error processing JSON-LD on {target}: {err}")
            continue

    return validated_items


def _extract_and_add(
    node: dict,
    current_page_url: str,
    base_url: str,
    brand_name: str,
    segment: str,
    rank: int,
    seen_urls: Set[str],
    out_list: List[Dict[str, Any]],
) -> None:
    prod_url = node.get("url") or current_page_url
    if not prod_url or not isinstance(prod_url, str):
        return
    if not prod_url.startswith("http"):
        prod_url = urljoin(base_url, prod_url)
    if prod_url in seen_urls:
        return
    seen_urls.add(prod_url)

    # Extract pricing and availability from offers structure
    offers = node.get("offers", {})
    price = 0.0
    in_stock = True
    if isinstance(offers, list) and offers:
        offers = offers[0]
    if isinstance(offers, dict):
        price = offers.get("price") or offers.get("lowPrice") or 0.0
        availability = str(offers.get("availability", "")).lower()
        if availability:
            in_stock = "outofstock" not in availability

    # Extract primary high-resolution imagery — resolve relative paths
    # (e.g. "/uploads/x.webp") against base_url, otherwise the validator
    # rejects the whole item for not having an absolute image URL.
    images = node.get("image", "")
    raw_image_list: List[str] = []
    if isinstance(images, str) and images:
        raw_image_list = [images]
    elif isinstance(images, list):
        raw_image_list = [str(i) for i in images if isinstance(i, str)]
    image_array = [urljoin(base_url, img) if not img.startswith("http") else img for img in raw_image_list]
    primary_img = image_array[0] if image_array else ""

    candidate = {
        "rank_position": rank,
        "title": node.get("name", ""),
        "product_url": prod_url,
        "published_at": "",
        "price_lkr": price,
        "primary_image_url": primary_img,
        "image_array": image_array,
        "shopify_tags": [],
        "product_type": node.get("category", "apparel"),
        "source_name": brand_name,
        "source_type": "tier2_json_ld",
        "market_segment": segment,
        "in_stock": in_stock,
        "description": str(node.get("description", ""))[:500],
    }
    clean = GarmentValidator.validate_and_sanitize(candidate)
    if clean:
        out_list.append(clean)


def _build_target_web_urls(configured_endpoints: List[str], sitemap_urls: Optional[List[str]]) -> List[str]:
    """Combine clean collection routes with sitemap discovered links."""
    web_urls: List[str] = []
    
    if sitemap_urls:
        web_urls.extend(sitemap_urls[:10])

    for ep in configured_endpoints or []:
        clean = ep.split("?")[0]
        if ".json" in clean:
            clean = "/collections/all" if clean in ["/products.json", "products.json"] else clean.replace("/products.json", "").replace(".json", "")
        if clean and clean not in web_urls:
            web_urls.append(clean)

    if not web_urls or web_urls == ["/collections/all"]:
        for fb in ["/collections/all", "/collections/new-arrivals", "/shop", "/women"]:
            if fb not in web_urls:
                web_urls.append(fb)
    return web_urls

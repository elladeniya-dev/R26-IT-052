"""
Tier 2: Schema.org JSON-LD Microdata Extraction Engine.
Extracts structured product data embedded in <script type="application/ld+json"> blocks across
category grids or individual sitemap URLs without visual DOM CSS dependencies.
"""
import json
import logging
import re
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

from services.garment_validator import GarmentValidator
from services.spec_parser import parse_spec_fields

logger = logging.getLogger("OutfitIQ.Tier2JsonLD")
MAX_ITEMS_PER_STORE = 100
DEFAULT_TIMEOUT = 8
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
}
PRICE_REGEX = re.compile(r"(?:Rs\.?|LKR)\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)
OUT_OF_STOCK_PATTERN = re.compile(r"out\s*of\s*stock|sold\s*out", re.IGNORECASE)


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


MAX_DETAIL_PAGES = 30
_EXCLUDED_LINK_KEYWORDS = (
    "/account", "/cart", "/contact", "/about", "/faq", "/login", "/terms",
    "/blog", "/policy", "/policies", "/checkout", "/search", "/wishlist",
)
_TRAILING_ID = re.compile(r"/\d{3,}(?:[/?#]|$)")


def _find_product_detail_links(listing_html: str, base_url: str) -> List[str]:
    """
    Fallback for platforms that render server-side but don't expose JSON-LD
    (confirmed via manual inspection on Chenara Dodge: /item/<slug>/<id> pages
    are plain static HTML with real product data, just no structured markup).
    Heuristic: a link is a product detail page if its path ends in a numeric
    ID and isn't an obvious nav/account/cart route.
    """
    soup = BeautifulSoup(listing_html, "html.parser")
    links: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip()
        if not href or not _TRAILING_ID.search(href):
            continue
        if any(bad in href.lower() for bad in _EXCLUDED_LINK_KEYWORDS):
            continue
        full_url = href if href.startswith("http") else urljoin(base_url, href)
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.add(full_url)
        if len(links) >= MAX_DETAIL_PAGES:
            break
    return sorted(links)


def _extract_detail_page(url: str, brand_name: str, segment: str, rank: int) -> Dict[str, Any]:
    resp = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
    if resp.status_code != 200:
        return {}

    page_text = resp.text
    soup = BeautifulSoup(page_text, "html.parser")

    og_title = soup.find("meta", property="og:title")
    title_tag = soup.find("title")
    title = (og_title.get("content") if og_title else None) or (title_tag.get_text() if title_tag else "")
    title = title.split("|")[0].strip()

    og_image = soup.find("meta", property="og:image")
    image_url = og_image.get("content", "") if og_image else ""

    price_match = PRICE_REGEX.search(page_text)
    price = float(price_match.group(1).replace(",", "")) if price_match else 0.0

    in_stock = not bool(OUT_OF_STOCK_PATTERN.search(page_text))

    # The spec sheet (Material/Color/etc.) is often embedded as an escaped
    # string inside a <script> blob rather than visible HTML — scan every
    # script block, not just the rendered DOM text.
    spec_fields = {}
    for script in soup.find_all("script"):
        txt = script.string or script.get_text() or ""
        if any(k in txt for k in ("Material", "Fabric", "Color", "Colour")):
            spec_fields = parse_spec_fields(txt)
            if spec_fields:
                break

    candidate = {
        "rank_position": rank,
        "title": title,
        "product_url": url,
        "published_at": "",
        "price_lkr": price,
        "primary_image_url": image_url,
        "image_array": [image_url] if image_url else [],
        "shopify_tags": [],
        "product_type": "apparel",
        "source_name": brand_name,
        "source_type": "tier2_static_detail",
        "market_segment": segment,
        "in_stock": in_stock,
        "desc_material": spec_fields.get("material", ""),
        "desc_color": spec_fields.get("color", ""),
        "desc_fit_type": spec_fields.get("fit_type", ""),
        "desc_style": spec_fields.get("style", ""),
    }
    return GarmentValidator.validate_and_sanitize(candidate)


def execute_tier2_static_detail_scrape(
    store_config: Dict[str, Any], sitemap_urls: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Fallback when standard JSON-LD parsing finds nothing but the store is
    still plain server-rendered HTML (no JS needed) — fetch listing pages for
    product links, then fetch each product page directly. Cheaper and more
    reliable than a full browser render (Tier 3) whenever it applies.
    """
    brand_name = str(store_config.get("brand_name", "Unknown"))
    base_url = str(store_config.get("base_url", "")).rstrip("/")
    segment = str(store_config.get("segment", "General"))
    endpoints = _build_target_web_urls(store_config.get("target_endpoints", []), sitemap_urls)

    detail_links: Set[str] = set()
    for ep in endpoints:
        target = urljoin(base_url, ep) if not ep.startswith("http") else ep
        try:
            resp = requests.get(target, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                detail_links.update(_find_product_detail_links(resp.text, base_url))
        except Exception as err:
            logger.debug(f"[Tier 2 Static Detail] Listing fetch error on {target}: {err}")
        if len(detail_links) >= MAX_DETAIL_PAGES:
            break

    validated_items: List[Dict[str, Any]] = []
    for rank, url in enumerate(sorted(detail_links)[:MAX_DETAIL_PAGES], start=1):
        try:
            item = _extract_detail_page(url, brand_name, segment, rank)
            if item:
                validated_items.append(item)
        except Exception as err:
            logger.debug(f"[Tier 2 Static Detail] Detail fetch error on {url}: {err}")

    return validated_items

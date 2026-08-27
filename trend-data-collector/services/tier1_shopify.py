"""
Tier 1: Shopify Direct JSON & Storefront Suggest AJAX Harvesting Engine.
Provides rapid (<500ms), structured fashion catalog retrieval with built-in tolerance
against Shopify 429 local_rate_limited Edge firewalls and automatic memory bounding.
"""
import time
import logging
from typing import List, Dict, Any, Set
from urllib.parse import urljoin
import requests

from services.garment_validator import GarmentValidator
from services.spec_parser import parse_spec_fields

logger = logging.getLogger("OutfitIQ.Tier1Shopify")

# High-yield search terms for gathering Sri Lankan fashion catalogs via Storefront AJAX
SUGGESTION_KEYWORDS: List[str] = ["dress", "top", "linen", "new", "casual", "wear", "saree", "blouse"]
MAX_ITEMS_PER_STORE: int = 100
DEFAULT_TIMEOUT: int = 7


def execute_tier1_shopify_json(store_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Query open Shopify JSON interfaces directly without DOM browser rendering.
    If traditional /products.json dumps trigger 429 throttling blocks, immediately transition
    to the open Storefront Suggestion AJAX framework.
    """
    brand_name = str(store_config.get("brand_name", "Unknown"))
    base_url = str(store_config.get("base_url", "")).rstrip("/")
    segment = str(store_config.get("segment", "General"))

    endpoints = ["/products.json?limit=250"]
    for ep in store_config.get("target_endpoints", []):
        if ".json" in ep and ep not in endpoints:
            endpoints.append(ep)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Connection": "keep-alive",
    }

    validated_items: List[Dict[str, Any]] = []
    seen_urls: Set[str] = set()
    rank = 1

    # 1. Primary Attempt: Batch /products.json database endpoints
    for ep in endpoints:
        target = urljoin(base_url, ep)
        try:
            resp = requests.get(target, headers=headers, timeout=DEFAULT_TIMEOUT)
            if resp.status_code != 200:
                continue

            data = resp.json()
            for item in data.get("products", []):
                if len(validated_items) >= MAX_ITEMS_PER_STORE:
                    break

                handle = item.get("handle")
                if not handle:
                    continue
                prod_url = f"{base_url}/products/{handle}"
                if prod_url in seen_urls:
                    continue
                seen_urls.add(prod_url)

                variants = item.get("variants", [])
                raw_price = variants[0].get("price", 0.0) if variants else 0.0
                compare_at = variants[0].get("compare_at_price") if variants else None
                in_stock = any(v.get("available") for v in variants) if variants else True
                images = [img.get("src", "") for img in item.get("images", []) if isinstance(img, dict)]
                image_alt_text = " ".join(
                    img.get("alt", "") or "" for img in item.get("images", []) if isinstance(img, dict)
                ).strip()
                body_html = item.get("body_html", "")
                spec_fields = parse_spec_fields(body_html)
                spec_color = spec_fields.get("color", "").split(",")[0].strip() if spec_fields.get("color") else ""

                candidate = {
                    "rank_position": rank,
                    "title": item.get("title", ""),
                    "product_url": prod_url,
                    "published_at": item.get("published_at") or item.get("created_at", ""),
                    "price_lkr": raw_price,
                    "original_price_lkr": _parse_compare_at_price(compare_at, raw_price),
                    "in_stock": in_stock,
                    "primary_image_url": images[0] if images else "",
                    "image_array": images,
                    "shopify_tags": _parse_tags(item.get("tags")),
                    "product_type": item.get("product_type", "apparel"),
                    "source_name": brand_name,
                    "source_type": "tier1_shopify_json",
                    "market_segment": segment,
                    "variant_color": _extract_variant_color(item, variants),
                    "description": _strip_html(body_html),
                    "image_alt_text": image_alt_text,
                    "desc_material": spec_fields.get("material", ""),
                    "desc_color": spec_color,
                    "desc_fit_type": spec_fields.get("fit_type", ""),
                    "desc_style": spec_fields.get("style", ""),
                }
                clean_item = GarmentValidator.validate_and_sanitize(candidate)
                if clean_item:
                    validated_items.append(clean_item)
                    rank += 1
        except Exception as err:
            logger.debug(f"[Tier 1] Non-fatal endpoint error on {target}: {err}")

    # 2. Resilient Fallback: If blocked by 429 local_rate_limited, activate Storefront Suggest AJAX bypass
    if not validated_items:
        _harvest_via_suggest_ajax(base_url, brand_name, segment, headers, seen_urls, validated_items, rank)

    return validated_items


def _harvest_via_suggest_ajax(
    base_url: str,
    brand_name: str,
    segment: str,
    headers: dict,
    seen_urls: Set[str],
    out_list: List[Dict[str, Any]],
    start_rank: int,
) -> None:
    """Execute rapid multi-keyword inventory aggregation via unblocked Storefront AJAX suggestion routing."""
    rank = start_rank
    for kw in SUGGESTION_KEYWORDS:
        if len(out_list) >= MAX_ITEMS_PER_STORE:
            break
            
        target = f"{base_url}/search/suggest.json?q={kw}&resources[type]=product&resources[limit]=25"
        try:
            resp = requests.get(target, headers=headers, timeout=DEFAULT_TIMEOUT - 1)
            if resp.status_code == 404:
                # 404 implies target is non-Shopify (e.g. WooCommerce/Magento)
                break
            if resp.status_code != 200:
                continue

            payload = resp.json()
            products = payload.get("resources", {}).get("results", {}).get("products", [])
            
            for item in products:
                if len(out_list) >= MAX_ITEMS_PER_STORE:
                    break
                    
                handle = item.get("handle") or ""
                raw_url = item.get("url", "")
                clean_path = raw_url.split("?")[0] if raw_url else f"/products/{handle}"
                prod_url = urljoin(base_url, clean_path)

                if prod_url in seen_urls or not prod_url.startswith("http"):
                    continue
                seen_urls.add(prod_url)

                raw_price = item.get("price") or item.get("price_min") or 0.0
                img = item.get("image") or item.get("featured_image") or ""
                if img and not img.startswith("http") and not img.startswith("//"):
                    img = urljoin(base_url, img)
                elif img.startswith("//"):
                    img = f"https:{img}"

                candidate = {
                    "rank_position": rank,
                    "title": item.get("title", ""),
                    "product_url": prod_url,
                    "published_at": "",
                    "price_lkr": raw_price,
                    "primary_image_url": img,
                    "image_array": [img] if img else [],
                    "shopify_tags": _parse_tags(item.get("tags")),
                    "product_type": item.get("type", "apparel"),
                    "source_name": brand_name,
                    "source_type": "tier1_shopify_json",
                    "market_segment": segment,
                }
                clean = GarmentValidator.validate_and_sanitize(candidate)
                if clean:
                    out_list.append(clean)
                    rank += 1
            time.sleep(0.05)  # Polite network interval
        except Exception as err:
            logger.debug(f"[Tier 1 Suggest] Error on keyword '{kw}': {err}")
            continue


def _parse_compare_at_price(compare_at, current_price) -> float:
    """compare_at_price is Shopify's 'original price' field — only meaningful
    (i.e. actually a discount) when it's set and higher than the current price."""
    try:
        compare_at = float(compare_at) if compare_at else 0.0
    except (TypeError, ValueError):
        return 0.0
    return compare_at if compare_at > float(current_price or 0) else 0.0


def _extract_variant_color(item: Dict[str, Any], variants: List[Dict[str, Any]]) -> str:
    """
    Shopify stores each product's option names in item['options'] (e.g. ['Color', 'Size'])
    and each variant carries the matching values in option1/option2/option3. If one of the
    product's declared options is a color option, read it straight from the first variant —
    this is structured, store-declared data, far more reliable than guessing from text.
    """
    if not variants:
        return ""
    options = item.get("options", [])
    for idx, opt in enumerate(options):
        name = str(opt.get("name", "")).strip().lower() if isinstance(opt, dict) else str(opt).strip().lower()
        if name in ("color", "colour"):
            value = variants[0].get(f"option{idx + 1}", "")
            return str(value).strip() if value else ""
    return ""


def _strip_html(html: str) -> str:
    if not html:
        return ""
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()[:500]


def _parse_tags(raw_tags: any) -> List[str]:
    if isinstance(raw_tags, list):
        return [t.strip().lower() for t in raw_tags if isinstance(t, str)]
    elif isinstance(raw_tags, str) and raw_tags:
        return [t.strip().lower() for t in raw_tags.split(",")]
    return []

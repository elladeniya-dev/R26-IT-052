import logging
import requests
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def fetch_shopify_json(url: str, timeout: int = 20) -> Optional[Dict[str, Any]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        else:
            logging.warning(f"Failed to fetch {url}: Status {response.status_code}")
            return None
    except Exception as e:
        logging.warning(f"Error fetching Shopify JSON from {url}: {str(e)}")
        return None


def parse_shopify_tags(raw_tags: Any) -> List[str]:
    if isinstance(raw_tags, str):
        return [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
    elif isinstance(raw_tags, list):
        return [str(t).strip().lower() for t in raw_tags if str(t).strip()]
    return []


def collect_store_products_json(store_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    brand_name = store_config.get("brand_name", "Unknown")
    base_url = store_config.get("base_url", "")
    endpoints = store_config.get("target_endpoints", ["/products.json?limit=250"])
    market_segment = store_config.get("segment", "General")

    logging.info(f"--- [Tier 1: Shopify] Harvesting {brand_name} ---")

    all_garments = []
    seen_urls = set()
    rank_counter = 1

    for endpoint in endpoints:
        target_url = urljoin(base_url, endpoint)
        logging.info(f"Querying endpoint: {target_url}")

        data = fetch_shopify_json(target_url)
        if not data or "products" not in data:
            logging.warning(f"No valid products array returned from {target_url}")
            continue

        products_list = data.get("products", [])
        for item in products_list:
            handle = item.get("handle")
            if not handle:
                continue

            product_url = f"{base_url.rstrip('/')}/products/{handle}"
            if product_url in seen_urls:
                continue
            seen_urls.add(product_url)

            title = item.get("title", "").strip()
            if not title:
                continue

            # Extract timestamps
            published_at = item.get("published_at") or item.get("created_at", "")

            # Extract variant pricing
            variants = item.get("variants", [])
            price_lkr = 0.0
            if variants and isinstance(variants, list):
                try:
                    price_val = variants[0].get("price", "0")
                    price_lkr = float(str(price_val).replace(",", ""))
                except (ValueError, TypeError):
                    price_lkr = 0.0

            # Extract images for CV / YOLOv8 analysis
            images = item.get("images", [])
            image_urls = []
            primary_image = ""
            if images and isinstance(images, list):
                for img in images:
                    src = img.get("src") if isinstance(img, dict) else str(img)
                    if src:
                        image_urls.append(src)
                if image_urls:
                    primary_image = image_urls[0]

            # Parse rich design tags
            tags = parse_shopify_tags(item.get("tags"))
            product_type = (item.get("product_type") or "").strip().lower()

            all_garments.append(
                {
                    "rank_position": rank_counter,
                    "title": title,
                    "product_url": product_url,
                    "published_at": str(published_at),
                    "price_lkr": price_lkr,
                    "primary_image_url": primary_image,
                    "image_array": image_urls[:5],  # Preserve top 5 high-res images
                    "shopify_tags": tags,
                    "product_type": product_type,
                    "source_name": brand_name,
                    "source_type": "shopify_json",
                    "market_segment": market_segment,
                }
            )
            rank_counter += 1

    logging.info(
        f"Collected {len(all_garments)} garments from {brand_name} (Shopify JSON)"
    )
    return all_garments


def collect_all_tier1_stores(stores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    combined_results = []
    for store in stores:
        try:
            garments = collect_store_products_json(store)
            combined_results.extend(garments)
        except Exception as e:
            logging.error(f"Failed harvesting store {store.get('brand_name')}: {e}")
    return combined_results

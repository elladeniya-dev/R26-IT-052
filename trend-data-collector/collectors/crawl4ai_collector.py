import asyncio
import logging
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    logging.warning(
        "crawl4ai is not imported or installed in this Python environment. Will use legacy fallback."
    )


async def crawl_store_async(store_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    brand_name = store_config.get("brand_name", "Unknown")
    base_url = store_config.get("base_url", "")
    endpoints = store_config.get("target_endpoints", ["/women"])
    market_segment = store_config.get("segment", "General")

    logging.info(
        f"--- [Tier 2: Crawl4AI] Harvester initialized for {brand_name} ---"
    )
    results = []
    rank_counter = 1
    seen_urls = set()

    if not CRAWL4AI_AVAILABLE:
        logging.warning(
            f"Crawl4AI unavailable; attempting HTTP fallback for {brand_name}"
        )
        return _http_fallback_harvest(store_config)

    try:
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0 Safari/537.36"
            ),
        )
        # Configure automatic scrolling to trigger lazy loaded product card grids
        run_config = CrawlerRunConfig(
            word_count_threshold=5,
            page_timeout=30000,
            magic=True,  # Enables automatic anti-bot & ad stripping
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            for endpoint in endpoints:
                target_url = urljoin(base_url, endpoint)
                logging.info(f"Crawl4AI navigating to: {target_url}")

                result = await crawler.arun(url=target_url, config=run_config)
                if not result.success:
                    logging.warning(
                        f"Crawl failed for {target_url}: {result.error_message}"
                    )
                    continue

                # Parse cleaned markdown and HTML from Crawl4AI result
                html_content = result.html or ""
                if html_content:
                    extracted = _extract_products_from_html(
                        html_content,
                        base_url,
                        brand_name,
                        market_segment,
                        seen_urls,
                        rank_counter,
                    )
                    results.extend(extracted)
                    rank_counter += len(extracted)

    except Exception as e:
        logging.error(f"Error executing Crawl4AI for {brand_name}: {str(e)}")
        logging.info("Falling back to synchronous HTTP harvesting.")
        return _http_fallback_harvest(store_config)

    logging.info(
        f"Collected {len(results)} garments from {brand_name} (Crawl4AI Pipeline)"
    )
    return results


def _extract_products_from_html(
    html: str,
    base_url: str,
    brand_name: str,
    segment: str,
    seen: set,
    start_rank: int,
) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    products = []
    rank = start_rank

    # Hunt for product card anchors common in SL stores (Odel, Cool Planet, Nolimit, House of Fashions)
    product_links = soup.find_all(
        "a",
        href=lambda href: href
        and any(
            k in href.lower()
            for k in [
                "/product/",
                "/p/",
                "/item/",
                "/buy/",
                "-p-",
                "/clothing/",
                "/women/",
            ]
        ),
    )

    for link in product_links:
        href = link.get("href")
        prod_url = urljoin(base_url, href)
        if prod_url in seen:
            continue

        text = link.get_text(" ", strip=True)
        img = link.find("img")
        img_url = ""
        if img:
            img_url = (
                img.get("src")
                or img.get("data-src")
                or img.get("data-original")
                or ""
            )
            if not text:
                text = img.get("alt") or img.get("title") or ""

        text = " ".join(text.split()).strip()
        if (
            not text
            or len(text) < 4
            or any(
                x in text.lower()
                for x in ["cart", "quick view", "sale", "login", "home", "menu"]
            )
        ):
            continue

        seen.add(prod_url)
        products.append(
            {
                "rank_position": rank,
                "title": text,
                "product_url": prod_url,
                "published_at": "",
                "price_lkr": 0.0,
                "primary_image_url": img_url,
                "image_array": [img_url] if img_url else [],
                "shopify_tags": [],
                "product_type": "apparel",
                "source_name": brand_name,
                "source_type": "crawl4ai_extraction",
                "market_segment": segment,
            }
        )
        rank += 1

    return products


def _http_fallback_harvest(store_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    import requests

    brand_name = store_config.get("brand_name", "Unknown")
    base_url = store_config.get("base_url", "")
    endpoints = store_config.get("target_endpoints", ["/women"])
    segment = store_config.get("segment", "General")

    results = []
    seen = set()
    rank = 1

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        )
    }

    for endpoint in endpoints:
        url = urljoin(base_url, endpoint)
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                extracted = _extract_products_from_html(
                    resp.text, base_url, brand_name, segment, seen, rank
                )
                results.extend(extracted)
                rank += len(extracted)
        except Exception as e:
            logging.warning(f"HTTP fallback error for {url}: {e}")

    return results


def collect_store_crawl4ai(store_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Synchronous wrapper for asynchronous crawl4ai extraction."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            try:
                import nest_asyncio

                nest_asyncio.apply()
                return loop.run_until_complete(crawl_store_async(store_config))
            except ImportError:
                logging.warning("nest_asyncio missing in running event loop; using HTTP fallback.")
                return _http_fallback_harvest(store_config)
        else:
            return asyncio.run(crawl_store_async(store_config))
    except RuntimeError:
        return asyncio.run(crawl_store_async(store_config))


def collect_all_tier2_stores(stores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    combined_results = []
    for store in stores:
        try:
            garments = collect_store_crawl4ai(store)
            combined_results.extend(garments)
        except Exception as e:
            logging.error(
                f"Failed Tier 2 harvest for {store.get('brand_name')}: {e}"
            )
    return combined_results

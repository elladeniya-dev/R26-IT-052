"""
Sitemap XML Discovery Engine for OutfitIQ.
Dynamically locates active e-commerce fashion category and product URLs by parsing merchant
sitemaps, eliminating brittle manual endpoint maintenance and bypassing routing blocks.
"""
import logging
import xml.etree.ElementTree as ET
from typing import List, Set
from urllib.parse import urljoin, urlparse
import requests

logger = logging.getLogger("OutfitIQ.SitemapDiscovery")

# Keywords identifying high-value women's fashion listing pages in sitemaps
FASHION_CATEGORY_KEYWORDS: Set[str] = {
    "women", "dress", "dresses", "top", "tops", "casual", "casualwear", 
    "formal", "saree", "kurta", "partywear", "blouse", "skirts", "bottoms", 
    "jackets", "apparel", "clothing", "new-arrivals", "workwear", "lounge"
}

# Paths typically excluded from garment harvesting
EXCLUDE_URL_PATTERNS: Set[str] = {
    "/account", "/cart", "/checkout", "/contact", "/about", "/faq", 
    "/privacy", "/terms", "/blog", "/pages/", "/search", "/return"
}


def get_default_request_headers() -> dict:
    """Return hardened browser headers for automated reconnaissance."""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }


def discover_catalog_urls(base_url: str, max_urls: int = 15) -> List[str]:
    """
    Query a merchant's sitemap.xml or sitemap_products_1.xml to autonomously uncover
    active clothing category and collection routes.
    
    Args:
        base_url: Root website URL (e.g., 'https://odel.lk')
        max_urls: Bounded cap on returned discovery URLs to maintain efficiency.
        
    Returns:
        List of absolute URLs optimized for fashion item extraction.
    """
    if not base_url or not base_url.startswith("http"):
        return []

    clean_base = base_url.rstrip("/")
    candidate_sitemaps = [
        f"{clean_base}/sitemap.xml",
        f"{clean_base}/sitemap_products_1.xml",
        f"{clean_base}/sitemap-index.xml",
    ]

    discovered_links: List[str] = []
    seen: Set[str] = set()
    headers = get_default_request_headers()

    for sitemap_url in candidate_sitemaps:
        if len(discovered_links) >= max_urls:
            break
        try:
            resp = requests.get(sitemap_url, headers=headers, timeout=6)
            if resp.status_code != 200:
                continue

            content_text = resp.text
            # Basic parsing optimization: extract <loc> contents without failing on strict XML schema issues
            lines = content_text.replace(">", "> \n").replace("<", "\n<").splitlines()
            in_loc = False
            current_url = ""

            for line in lines:
                line_str = line.strip()
                if line_str.startswith("<loc>"):
                    in_loc = True
                    # Check inline <loc>http...</loc>
                    parts = line_str.replace("<loc>", "").replace("</loc>", "").strip()
                    if parts.startswith("http"):
                        _evaluate_and_add_url(parts, clean_base, seen, discovered_links, max_urls)
                elif line_str.startswith("</loc>"):
                    in_loc = False
                elif in_loc and line_str.startswith("http"):
                    _evaluate_and_add_url(line_str, clean_base, seen, discovered_links, max_urls)

                if len(discovered_links) >= max_urls:
                    break

            if discovered_links:
                logger.debug(f"[Sitemap Discovery] Uncovered {len(discovered_links)} URLs from {sitemap_url}")
                break

        except Exception as err:
            logger.debug(f"[Sitemap Discovery] Non-fatal timeout/error on {sitemap_url}: {err}")
            continue

    return discovered_links


def _evaluate_and_add_url(url: str, base_domain: str, seen: Set[str], out_list: List[str], max_urls: int) -> None:
    """Filter candidate URL against fashion keywords and security exclusions."""
    if len(out_list) >= max_urls or url in seen:
        return

    # Security check: verify link stays on same host domain
    if urlparse(url).netloc.lower() != urlparse(base_domain).netloc.lower():
        return

    url_lower = url.lower()
    # Exclude system/admin pathways
    if any(ex in url_lower for ex in EXCLUDE_URL_PATTERNS):
        return

    # Match fashion intent in path or keep if it represents a product detail link
    is_fashion = any(kw in url_lower for kw in FASHION_CATEGORY_KEYWORDS)
    is_product_detail = "/products/" in url_lower or "/dp/" in url_lower or "/item/" in url_lower

    if is_fashion or is_product_detail:
        seen.add(url)
        out_list.append(url)

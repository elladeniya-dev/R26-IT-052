"""
OutfitIQ Enterprise Data Harvester & Multi-Tier Orchestrator.
Coordinates automated catalog discovery, schema validation, and multi-tier scraping
(Shopify API -> Schema.org -> Gemini Autonomous AI / Smart DOM) with zero over-engineering,
uniform error resilience, and automated memory bounds.
"""
import asyncio
import logging
from typing import List, Dict, Any

from services.garment_validator import GarmentValidator
from services.sitemap_discovery import discover_catalog_urls
from services.tier1_shopify import execute_tier1_shopify_json
from services.tier2_jsonld import execute_tier2_json_ld
from services.tier3_smart_dom import execute_tier3_smart_dom_async

# Ensure public re-exports are available for backwards compatibility with existing pipelines
__all__ = [
    "GarmentValidator",
    "harvest_store_catalog",
    "execute_tier1_shopify_json",
    "execute_tier2_json_ld",
    "execute_tier3_smart_dom_async",
    "execute_tier3_smart_dom"
]

logger = logging.getLogger("OutfitIQ.Harvester")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def execute_tier3_smart_dom(store_config: Dict[str, Any], sitemap_urls: list = None) -> List[Dict[str, Any]]:
    """Synchronous facade wrapper around asynchronous Crawl4AI / Playwright routines."""
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            return asyncio.ensure_future(execute_tier3_smart_dom_async(store_config, sitemap_urls))
    except RuntimeError:
        pass
    return asyncio.run(execute_tier3_smart_dom_async(store_config, sitemap_urls))


def harvest_store_catalog(store_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Orchestrate multi-tiered fashion trend data harvesting for a single e-commerce platform.
    
    Workflow:
    1. Check Tier 1 (Shopify Direct JSON & Storefront Suggest AJAX API). If successful (>=3 items), short-circuit immediately.
    2. Run automated Sitemap XML Discovery to locate dynamic product and collection routes without hardcoding.
    3. Try Tier 2 (JSON-LD Schema microdata parsing) using both configured and sitemap-discovered routes.
    4. Fall back to Tier 3 (Autonomous Gemini Flash AI Scraper / Smart DOM extraction).
    """
    brand = str(store_config.get("brand_name", "Unknown"))
    base_url = str(store_config.get("base_url", ""))
    configured_tier = str(store_config.get("ingestion_tier", "tier1_shopify_json"))

    logger.info(f"==> Initiating extraction for: {brand} ({base_url}) | Targeted Tier: {configured_tier}")
    
    garments: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # STEP 1: Fast Tier 1 (Shopify Direct API & Storefront AJAX Bypass)
    # -------------------------------------------------------------------------
    if configured_tier in ["shopify_json_direct", "tier1_shopify_json", "unknown"]:
        try:
            logger.info(f"   [Tier 1] Checking direct Shopify interfaces & Storefront AJAX on {brand}...")
            garments = execute_tier1_shopify_json(store_config)
            if len(garments) >= 3:
                logger.info(f"   ---> [Success] Tier 1 acquired {len(garments)} validated garments.")
                return garments
            else:
                logger.debug(f"   [Tier 1] Insufficient catalog records ({len(garments)}). Advancing to Tier 2/3.")
        except Exception as err:
            logger.debug(f"   [Tier 1] Error encountered on {brand}: {err}")

    # -------------------------------------------------------------------------
    # STEP 2: Autonomous Sitemap XML Discovery Radar
    # -------------------------------------------------------------------------
    sitemap_urls = discover_catalog_urls(base_url, max_urls=12)

    # -------------------------------------------------------------------------
    # STEP 3: Tier 2 Schema.org JSON-LD Microdata
    # -------------------------------------------------------------------------
    if not garments and (configured_tier in ["shopify_json_direct", "json_ld_schema", "tier1_shopify_json", "tier2_json_ld", "unknown"]):
        try:
            logger.info(f"   [Tier 2] Analyzing embedded Schema.org JSON-LD microdata on {brand}...")
            garments = execute_tier2_json_ld(store_config, sitemap_urls=sitemap_urls)
            if len(garments) >= 3:
                logger.info(f"   ---> [Success] Tier 2 acquired {len(garments)} validated garments.")
                return garments
        except Exception as err:
            logger.debug(f"   [Tier 2] Error encountered on {brand}: {err}")

    # -------------------------------------------------------------------------
    # STEP 4: Tier 3 Autonomous AI Scraper (Gemini Flash) & Smart DOM Parsing
    # -------------------------------------------------------------------------
    if not garments:
        try:
            logger.info(f"   [Tier 3] Engaging Autonomous Gemini AI & Smart DOM extraction on {brand}...")
            garments = execute_tier3_smart_dom(store_config, sitemap_urls=sitemap_urls)
            if garments:
                logger.info(f"   ---> [Success] Tier 3 acquired {len(garments)} validated garments.")
        except Exception as err:
            logger.error(f"   [Tier 3] Fatal browser extraction failure on {brand}: {err}")

    if not garments:
        logger.warning(f"[WARNING] {brand} yielded 0 validated garments across all extraction layers.")

    return garments

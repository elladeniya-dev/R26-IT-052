import json
import logging
import time
from pathlib import Path

from config.target_stores import (
    SRI_LANKA_TARGET_STORES,
    TIER_1_SHOPIFY,
    TIER_2_CRAWL4AI,
    SEGMENT_HIGH_VELOCITY_BOUTIQUES,
    SEGMENT_MASS_MARKET_DEPARTMENT,
    SEGMENT_SPECIALTY_WORKWEAR,
)
from collectors.shopify_collector import collect_store_products_json
from collectors.crawl4ai_collector import collect_store_crawl4ai
from services.trend_mapping_service import map_products_to_trend_observations

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

OUTPUT_DIR = Path("output")
COMBINED_GARMENTS_FILE = OUTPUT_DIR / "combined_srilanka_raw_garments.json"
COMBINED_OBSERVATIONS_FILE = (
    OUTPUT_DIR / "combined_srilanka_trend_observations.json"
)


def save_json(file_path: Path, data: any) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def run_hybrid_harvester(
    target_stores: list = None, max_stores_per_segment: int = None
) -> dict:
    stores_to_harvest = target_stores or SRI_LANKA_TARGET_STORES
    if max_stores_per_segment:
        filtered = []
        counts = {}
        for s in stores_to_harvest:
            seg = s.get("segment", "General")
            counts[seg] = counts.get(seg, 0) + 1
            if counts[seg] <= max_stores_per_segment:
                filtered.append(s)
        stores_to_harvest = filtered

    logging.info(
        f"=== Starting OutfitIQ Hybrid Two-Tier Harvester ({len(stores_to_harvest)} Stores) ==="
    )
    start_time = time.time()

    total_garments = []
    total_observations = []
    store_summaries = []
    segment_counts = {
        SEGMENT_HIGH_VELOCITY_BOUTIQUES: 0,
        SEGMENT_MASS_MARKET_DEPARTMENT: 0,
        SEGMENT_SPECIALTY_WORKWEAR: 0,
    }

    for store in stores_to_harvest:
        brand = store.get("brand_name", "Unknown")
        segment = store.get("segment", "General")
        tier = store.get("ingestion_tier", TIER_1_SHOPIFY)

        logging.info(
            f"\n---> Preparing ingestion for [{brand}] ({segment}) via [{tier}]"
        )
        garments = []

        try:
            if tier == TIER_1_SHOPIFY:
                garments = collect_store_products_json(store)
                if not garments:
                    logging.info(
                        f"No Shopify JSON items returned for {brand}; attempting Tier 2 Crawl4AI fallback..."
                    )
                    garments = collect_store_crawl4ai(store)
            elif tier == TIER_2_CRAWL4AI:
                garments = collect_store_crawl4ai(store)
            else:
                logging.warning(f"Unknown tier {tier} for {brand}. Skipping.")

        except Exception as e:
            logging.error(f"Error harvesting store {brand}: {e}")

        # Map collected garments to trend observations
        observations = map_products_to_trend_observations(
            products=garments,
            source_name=brand,
            source_type=tier,
        )

        # Store statistics
        store_summaries.append(
            {
                "brand_name": brand,
                "domain": store.get("domain"),
                "segment": segment,
                "ingestion_tier": tier,
                "garments_count": len(garments),
                "observations_count": len(observations),
            }
        )

        total_garments.extend(garments)
        total_observations.extend(observations)
        if segment in segment_counts:
            segment_counts[segment] += len(garments)

        # Save store-specific JSON for easier auditing
        safe_name = brand.lower().replace(" ", "_").replace("&", "and")
        save_json(OUTPUT_DIR / f"{safe_name}_garments.json", garments)

        time.sleep(0.5)  # Polite spacing between requests

    # Save combined outputs
    save_json(COMBINED_GARMENTS_FILE, total_garments)
    save_json(COMBINED_OBSERVATIONS_FILE, total_observations)

    elapsed = round(time.time() - start_time, 2)
    logging.info(f"\n=== Harvester Completed in {elapsed}s ===")
    logging.info(f"Total Raw Garments Collected: {len(total_garments)}")
    logging.info(f"Total Trend Observations Derived: {len(total_observations)}")

    return {
        "elapsed_seconds": elapsed,
        "total_stores": len(stores_to_harvest),
        "total_garments": len(total_garments),
        "total_observations": len(total_observations),
        "segment_garments_count": segment_counts,
        "store_summaries": store_summaries,
        "combined_garments_file": str(COMBINED_GARMENTS_FILE),
        "combined_observations_file": str(COMBINED_OBSERVATIONS_FILE),
        "top_observations": total_observations[:20],
    }


def main():
    # Run across all target stores (or pass max_stores_per_segment for testing)
    result = run_hybrid_harvester()

    print("\n" + "=" * 60)
    print("OUTFITIQ TREND DATA COLLECTOR - EXECUTIVE SUMMARY")
    print("=" * 60)
    print(f"Time Elapsed:         {result['elapsed_seconds']}s")
    print(f"Target Stores:        {result['total_stores']}")
    print(f"Total Garments:       {result['total_garments']}")
    print(f"Derived Observations: {result['total_observations']}")
    print(f"Output Directory:     {OUTPUT_DIR.resolve()}")

    print("\nGarment Counts by Market Segment:")
    for seg, count in result["segment_garments_count"].items():
        print(f"  - {seg}: {count}")

    print("\nStore Breakdown (Top 10):")
    for summary in result["store_summaries"][:10]:
        print(
            f"  * {summary['brand_name']} ({summary['ingestion_tier']}) -> "
            f"{summary['garments_count']} garments | {summary['observations_count']} trend hits"
        )

    print("\nTop Derived Trend Signals:")
    for obs in result["top_observations"][:10]:
        print(
            f"  # [{obs['source_name']}] {obs['attribute_type']}: '{obs['attribute_value']}' "
            f"(Mentions: {obs['mention_count']} | Segment: {obs.get('market_segment', 'N/A')})"
        )
    print("=" * 60)


if __name__ == "__main__":
    main()

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from config.target_stores import (
    SRI_LANKA_TARGET_STORES,
    TIER_1_SHOPIFY,
    SEGMENT_HIGH_VELOCITY_BOUTIQUES,
    SEGMENT_MASS_MARKET_DEPARTMENT,
    SEGMENT_SPECIALTY_WORKWEAR,
)
from services.harvester import harvest_store_catalog

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

OUTPUT_DIR = Path("output")
COMBINED_GARMENTS_FILE = OUTPUT_DIR / "combined_srilanka_raw_garments.json"


def save_json(file_path: Path, data: any) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
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

    run_timestamp = datetime.now().strftime("run_%Y-%m-%d_%H%M%S")
    run_dir = OUTPUT_DIR / run_timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    logging.info(
        f"=== Starting OutfitIQ Multi-Tiered Data Harvesting Pipeline ({len(stores_to_harvest)} Stores) | Run ID: {run_timestamp} ==="
    )
    start_time = time.time()

    total_garments = []
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

        garments = []

        try:
            garments = harvest_store_catalog(store)
        except Exception as e:
            logging.error(f"Error harvesting store {brand}: {e}")

        # Store statistics
        store_summaries.append(
            {
                "brand_name": brand,
                "domain": store.get("domain"),
                "segment": segment,
                "ingestion_tier": tier,
                "garments_count": len(garments),
            }
        )

        total_garments.extend(garments)
        if segment in segment_counts:
            segment_counts[segment] += len(garments)

        # Save store-specific JSON into timestamped run directory
        safe_name = brand.lower().replace(" ", "_").replace("&", "and")
        save_json(run_dir / f"{safe_name}_garments.json", garments)

        time.sleep(0.5)  # Polite spacing between requests

    # Save immutable timestamped snapshot inside run_dir
    run_combined_garments = run_dir / "combined_srilanka_raw_garments.json"
    save_json(run_combined_garments, total_garments)

    # Save summary metadata of this execution run
    metadata = {
        "run_id": run_timestamp,
        "timestamp": datetime.now().isoformat(),
        "total_stores": len(stores_to_harvest),
        "total_garments": len(total_garments),
        "run_directory": str(run_dir),
    }
    save_json(run_dir / "run_metadata.json", metadata)

    elapsed = round(time.time() - start_time, 2)
    logging.info(f"\n=== Harvester Completed in {elapsed}s | Saved to: {run_dir} ===")
    logging.info(f"Total Raw Garments Collected: {len(total_garments)}")

    return {
        "elapsed_seconds": elapsed,
        "total_stores": len(stores_to_harvest),
        "total_garments": len(total_garments),
        "run_directory": str(run_dir.resolve()),
        "segment_garments_count": segment_counts,
        "store_summaries": store_summaries,
        "combined_garments_file": str(run_combined_garments),
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
    print(f"Run Output Directory: {result['run_directory']}")
    print(f"Latest Mirror Path:   {OUTPUT_DIR.resolve()}")

    print("\nGarment Counts by Market Segment:")
    for seg, count in result["segment_garments_count"].items():
        print(f"  - {seg}: {count}")

    print("\nStore Breakdown (Top 10):")
    for summary in result["store_summaries"][:10]:
        print(f"  * {summary['brand_name']} ({summary['ingestion_tier']}) -> {summary['garments_count']} garments")
    print("=" * 60)
    print("Run `python app/pipeline/generate_trend_observations.py` + `python app/pipeline/compute_trend_signals.py`")
    print("from the project root to turn this raw snapshot into real trend signals.")


if __name__ == "__main__":
    main()

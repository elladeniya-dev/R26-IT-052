#!/usr/bin/env python3
"""
Source Verifier & Capability Profiler for OutfitIQ Research Engine
Confirms the exact optimal harvesting tier for all 26 Sri Lankan target stores without blind fallback.
Guarantees long-term research reliability by benchmarking every source and reporting broken routes.
"""
import sys
import json
import logging
import time
from typing import Dict, Any, List

from config.target_stores import SRI_LANKA_TARGET_STORES
from services.harvester import (
    execute_tier1_shopify_json,
    execute_tier2_json_ld,
    execute_tier3_smart_dom,
    _convert_to_web_endpoints
)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")

def verify_and_profile_store(store: Dict[str, Any], index: int, total: int) -> Dict[str, Any]:
    brand = store.get("brand_name", "Unknown")
    domain = store.get("domain", "")
    endpoints = store.get("target_endpoints", [])
    
    logging.info(f"\n=======================================================================")
    logging.info(f"[{index}/{total}] PROFILING SOURCE: {brand} ({domain})")
    logging.info(f"=======================================================================")
    
    report = {
        "brand_name": brand,
        "domain": domain,
        "segment": store.get("segment", ""),
        "original_endpoints": endpoints,
        "confirmed_tier": "NONE",
        "status": "FAILED",
        "items_extracted": 0,
        "sample_title": "",
        "sample_price_lkr": 0.0,
        "execution_time_sec": 0.0,
        "notes": ""
    }
    
    start_time = time.time()
    
    # 1. Check Tier 1 (Shopify Direct API)
    logging.info(f"   [Step 1] Testing Tier 1 (Shopify JSON Direct API) on {brand}...")
    try:
        t1_items = execute_tier1_shopify_json(store)
        if t1_items and len(t1_items) > 0:
            elapsed = round(time.time() - start_time, 2)
            logging.info(f"   ---> [SUCCESS] {brand} confirmed as TIER 1 (Shopify API). Extracted {len(t1_items)} items in {elapsed}s.")
            report.update({
                "confirmed_tier": "tier1_shopify_json",
                "status": "OPERATIONAL",
                "items_extracted": len(t1_items),
                "sample_title": t1_items[0].get("title", ""),
                "sample_price_lkr": t1_items[0].get("price_lkr", 0.0),
                "execution_time_sec": elapsed,
                "notes": "Fast direct JSON collection verified."
            })
            return report
        else:
            logging.info(f"   [Tier 1 Unavailable/Blocked] No valid products returned from JSON endpoints.")
    except Exception as e:
        logging.warning(f"   [Tier 1 Error] {e}")
        
    # 2. Check Tier 2 (JSON-LD Schema Microdata)
    logging.info(f"   [Step 2] Testing Tier 2 (JSON-LD Schema Microdata) on {brand}...")
    try:
        t2_items = execute_tier2_json_ld(store)
        if t2_items and len(t2_items) > 0:
            elapsed = round(time.time() - start_time, 2)
            logging.info(f"   ---> [SUCCESS] {brand} confirmed as TIER 2 (JSON-LD Schema). Extracted {len(t2_items)} items in {elapsed}s.")
            report.update({
                "confirmed_tier": "tier2_json_ld",
                "status": "OPERATIONAL",
                "items_extracted": len(t2_items),
                "sample_title": t2_items[0].get("title", ""),
                "sample_price_lkr": t2_items[0].get("price_lkr", 0.0),
                "execution_time_sec": elapsed,
                "notes": "SEO Schema structured data verified."
            })
            return report
        else:
            logging.info(f"   [Tier 2 Unavailable] No @type: Product Schema found on category pages.")
    except Exception as e:
        logging.warning(f"   [Tier 2 Error] {e}")

    # 3. Check Tier 3 (Smart DOM Extraction)
    logging.info(f"   [Step 3] Testing Tier 3 (Smart DOM AI Extraction + Lazy-Load Fix) on {brand}...")
    try:
        t3_items = execute_tier3_smart_dom(store)
        if t3_items and len(t3_items) > 0:
            elapsed = round(time.time() - start_time, 2)
            logging.info(f"   ---> [SUCCESS] {brand} confirmed as TIER 3 (Smart DOM). Extracted {len(t3_items)} items in {elapsed}s.")
            report.update({
                "confirmed_tier": "tier3_smart_dom",
                "status": "OPERATIONAL",
                "items_extracted": len(t3_items),
                "sample_title": t3_items[0].get("title", ""),
                "sample_price_lkr": t3_items[0].get("price_lkr", 0.0),
                "execution_time_sec": elapsed,
                "notes": "Visual DOM extraction with scroll hooks verified."
            })
            return report
        else:
            elapsed = round(time.time() - start_time, 2)
            logging.error(f"   ---> [FAILED] {brand} yielded 0 items under all 3 tiers! Route or DOM structure requires inspection.")
            report.update({
                "confirmed_tier": "FAILED",
                "status": "ACTION_REQUIRED",
                "items_extracted": 0,
                "execution_time_sec": elapsed,
                "notes": "All extraction methods returned 0 items. Target endpoints or selector logic may need adjustment."
            })
    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        logging.error(f"   ---> [FATAL ERROR] {brand} threw exception: {e}")
        report.update({
            "status": "ERROR",
            "execution_time_sec": elapsed,
            "notes": str(e)
        })
        
    return report

def main():
    logging.info("=== STARTING OUTFITIQ 26-SOURCE CAPABILITY & HEALTH VERIFICATION ===")
    total = len(SRI_LANKA_TARGET_STORES)
    results = []
    
    operational_count = 0
    failed_count = 0
    
    for idx, store in enumerate(SRI_LANKA_TARGET_STORES, 1):
        rep = verify_and_profile_store(store, idx, total)
        results.append(rep)
        if rep["status"] == "OPERATIONAL":
            operational_count += 1
        else:
            failed_count += 1
            
    summary = {
        "total_stores_audited": total,
        "operational": operational_count,
        "failed": failed_count,
        "store_profiles": results
    }
    
    out_file = "output/source_confirmation_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    logging.info(f"\n=======================================================================")
    logging.info(f"VERIFICATION COMPLETED: {operational_count}/{total} Stores Operational!")
    logging.info(f"Detailed profile report saved to: {out_file}")
    logging.info(f"=======================================================================")
    
    # Print summary table
    print("\n--- OUTFITIQ SOURCE VERIFICATION SUMMARY TABLE ---")
    print(f"{'BRAND NAME':<20} {'STATUS':<15} {'CONFIRMED TIER':<22} {'ITEMS':<8} {'SAMPLE PRICE LKR':<18}")
    print("-" * 85)
    for r in results:
        print(f"{r['brand_name']:<20} {r['status']:<15} {r['confirmed_tier']:<22} {r['items_extracted']:<8} {str(r['sample_price_lkr']):<18}")
    print("-" * 85)
    if failed_count > 0:
        print(f"\n[!] ACTION REQUIRED: {failed_count} sources require endpoint or selector adjustment before year-round research deployment.")
        for r in results:
            if r["status"] != "OPERATIONAL":
                print(f"   - {r['brand_name']} ({r['domain']}) -> Endpoints tried: {r['original_endpoints']}")

if __name__ == "__main__":
    main()

"""
Runs check_store_candidate's analysis across every store already in
config/target_stores.py — surfaces two things:
1. Any store tagged TIER_2_CRAWL4AI that's actually reachable via the
   Shopify JSON API (a free upgrade to richer, cheaper Tier 1 extraction).
2. Spec-sheet data quality per store, so low-yield stores are visible.
"""
from config.target_stores import SRI_LANKA_TARGET_STORES, TIER_1_SHOPIFY
from check_store_candidate import analyze_store

VERDICT_ORDER = {"strong": 0, "usable": 1, "weak": 2, "empty": 3, "not_shopify": 4, "unreachable": 5}


def audit_all():
    rows = []
    for store in SRI_LANKA_TARGET_STORES:
        brand = store["brand_name"]
        base_url = store["base_url"]
        configured_tier = store["ingestion_tier"]
        print(f"Checking {brand} ({base_url})...")
        result = analyze_store(base_url)
        rows.append((brand, configured_tier, result))

    rows.sort(key=lambda r: VERDICT_ORDER.get(r[2].get("verdict", r[2]["status"]), 9))

    print("\n" + "=" * 100)
    print(f"{'Brand':<20}{'Configured Tier':<16}{'Reality':<14}{'Material':<10}{'Color':<10}{'FitType':<10}{'Style':<10}{'Verdict'}")
    print("=" * 100)

    upgrade_candidates = []
    for brand, configured_tier, r in rows:
        is_shopify = r["status"] == "ok"
        reality = "SHOPIFY" if is_shopify else r["status"].upper()

        if is_shopify:
            n = r["sample_size"]
            fh = r["field_hits"]
            row = (
                f"{brand:<20}{configured_tier:<16}{reality:<14}"
                f"{fh['material']}/{n:<8}{fh['color']}/{n:<8}{fh['fit_type']}/{n:<8}{fh['style']}/{n:<8}"
                f"{r['verdict']}"
            )
            if configured_tier != TIER_1_SHOPIFY:
                upgrade_candidates.append(brand)
        else:
            row = f"{brand:<20}{configured_tier:<16}{reality:<14}{'-':<10}{'-':<10}{'-':<10}{'-':<10}{r.get('detail', '')}"
        print(row)

    print("=" * 100)
    if upgrade_candidates:
        print(f"\nUPGRADE CANDIDATES (currently non-Shopify tier, but Shopify JSON API works): {', '.join(upgrade_candidates)}")
        print("Consider switching these to TIER_1_SHOPIFY in target_stores.py for faster, richer, more reliable extraction.")
    else:
        print("\nNo upgrade candidates — every store's configured tier already matches reality.")


if __name__ == "__main__":
    audit_all()

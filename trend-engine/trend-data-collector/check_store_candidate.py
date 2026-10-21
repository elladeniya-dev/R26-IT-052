"""
Vets a candidate store URL before adding it to config/target_stores.py.
Usage: python check_store_candidate.py https://example.com

Checks: is it Shopify (fast Tier 1 path)? And of its products, what % have
a real store-written spec sheet (Material/Color/Fit Type/Style) in the
description, vs. relying on guesswork? High spec coverage = a great source,
matching what the "Joey Clothing" / "Carnage" examples looked like.
"""
import sys
from urllib.parse import urljoin

import requests

from services.spec_parser import parse_spec_fields

SAMPLE_SIZE = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OutfitIQ-ResearchBot"}


def analyze_store(base_url: str) -> dict:
    """Returns a result dict; never raises. status is one of:
    'unreachable', 'not_shopify', 'empty', 'ok'."""
    base_url = base_url.rstrip("/")
    target = urljoin(base_url, f"/products.json?limit={SAMPLE_SIZE}")

    try:
        resp = requests.get(target, headers=HEADERS, timeout=8)
    except Exception as err:
        return {"status": "unreachable", "detail": str(err)}

    if resp.status_code != 200:
        return {"status": "not_shopify", "detail": f"status {resp.status_code}"}

    try:
        products = resp.json().get("products", [])
    except ValueError:
        return {"status": "not_shopify", "detail": "invalid JSON"}

    if not products:
        return {"status": "empty", "detail": "0 products returned"}

    n = len(products)
    field_hits = {"material": 0, "color": 0, "fit_type": 0, "style": 0}
    has_variant_color = 0
    has_compare_at = 0

    for p in products:
        specs = parse_spec_fields(p.get("body_html", ""))
        for field in field_hits:
            if specs.get(field):
                field_hits[field] += 1

        variants = p.get("variants", [])
        options = p.get("options", [])
        if variants and any(str(o.get("name", "")).lower() in ("color", "colour") for o in options if isinstance(o, dict)):
            has_variant_color += 1
        if variants and variants[0].get("compare_at_price"):
            has_compare_at += 1

    avg_spec_coverage = sum(field_hits.values()) / (n * len(field_hits))
    if avg_spec_coverage > 0.5 or has_variant_color > n * 0.5:
        verdict = "strong"
    elif avg_spec_coverage > 0.15:
        verdict = "usable"
    else:
        verdict = "weak"

    return {
        "status": "ok",
        "sample_size": n,
        "field_hits": field_hits,
        "has_variant_color": has_variant_color,
        "has_compare_at": has_compare_at,
        "avg_spec_coverage": round(avg_spec_coverage, 2),
        "verdict": verdict,
    }


def print_report(base_url: str, result: dict) -> None:
    print(f"Checking {base_url} ...")
    if result["status"] == "unreachable":
        print(f"NOT REACHABLE: {result['detail']}")
        return
    if result["status"] == "not_shopify":
        print(f"NOT SHOPIFY (or blocked) — {result['detail']}. Would need Tier 2 (JSON-LD) or Tier 3.")
        return
    if result["status"] == "empty":
        print("Reachable, but returned 0 products. Skip or investigate manually.")
        return

    n = result["sample_size"]
    print(f"SHOPIFY CONFIRMED — {n} products sampled.\n")
    print("Description spec-sheet coverage (Material/Color/Fit Type/Style written explicitly):")
    for field, count in result["field_hits"].items():
        pct = round(100 * count / n)
        print(f"  {field:<10}: {count}/{n} ({pct}%)")
    print(f"\nStructured variant color option present: {result['has_variant_color']}/{n}")
    print(f"Discount pricing (compare_at_price) present: {result['has_compare_at']}/{n}")
    print()
    labels = {
        "strong": "Strong candidate — rich structured data. Add to target_stores.py as TIER_1_SHOPIFY.",
        "usable": "Usable — some structured data, will lean on keyword/NLP extraction for the rest.",
        "weak": "Weak — little to no structured spec data. Still scrapeable, but expect more Unknowns.",
    }
    print(f"VERDICT: {labels[result['verdict']]}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_store_candidate.py https://example.com")
        sys.exit(1)
    url = sys.argv[1]
    print_report(url, analyze_store(url))

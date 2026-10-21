"""Scores partner-catalogue products against the current trend snapshot. Pure: no DB, no HTTP.

contribution = trend_score x confidence_weight x match_weight x specificity
  confidence_weight  high 1.0, medium 0.6; low-confidence and falling trends are ignored
  match_weight       exact leaf 1.0, same family 0.5
  specificity        log(N/df)/log(N): an attribute carried by most of the batch says little
A product's trend_score is the sum of its strongest TOP_MATCHES contributions.
"""
from __future__ import annotations

import math

from app.ml.taxonomy import ATTR_TYPES, TAXONOMY_VERSION, canonical_attributes, family_of

CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.6}
FAMILY_WEIGHT = 0.5
TOP_MATCHES = 3
SPECIFICITY_FLOOR = 0.15
MIN_BATCH_FOR_SPECIFICITY = 10


def _match_kind(attr_type: str, trend_value: str, product_values: set[str]) -> str | None:
    if trend_value in product_values:
        return "exact"
    family = family_of(attr_type, trend_value)
    if family and any(family_of(attr_type, v) == family for v in product_values):
        return "family"
    return None


def score_products(products: list[dict], trends: list[dict]) -> tuple[list[dict], dict]:
    """products: descriptors with an 'id'. trends: rows with attr_type, attr_value, score, confidence."""
    rising = [
        t for t in trends
        if t["score"] > 0 and t.get("confidence") in CONFIDENCE_WEIGHT
        and t["attr_type"] in ATTR_TYPES and t["attr_value"] != "unknown"
    ]
    canon = [canonical_attributes(p) for p in products]
    n = len(products)

    hits: list[list[tuple[dict, str]]] = [[] for _ in products]
    carried = {id(t): 0 for t in rising}
    for i, attrs in enumerate(canon):
        for t in rising:
            kind = _match_kind(t["attr_type"], t["attr_value"], attrs.get(t["attr_type"], set()))
            if kind:
                hits[i].append((t, kind))
                carried[id(t)] += 1

    def specificity(trend: dict) -> float:
        df = carried[id(trend)]
        if n < MIN_BATCH_FOR_SPECIFICITY or df == 0:
            return 1.0
        return max(SPECIFICITY_FLOOR, math.log(n / df) / math.log(n))

    results = []
    for p, matched in zip(products, hits):
        contributions = []
        for t, kind in matched:
            weight = CONFIDENCE_WEIGHT[t["confidence"]] * (1.0 if kind == "exact" else FAMILY_WEIGHT)
            contributions.append({
                "attr_type": t["attr_type"], "attr_value": t["attr_value"], "match": kind,
                "trend_score": round(float(t["score"]), 4), "confidence": t["confidence"],
                "contribution": round(float(t["score"]) * weight * specificity(t), 4),
            })
        contributions.sort(key=lambda c: c["contribution"], reverse=True)
        results.append({
            "id": p["id"],
            "trend_score": round(sum(c["contribution"] for c in contributions[:TOP_MATCHES]), 4),
            "matches": contributions,
        })

    meta = {
        "taxonomy_version": TAXONOMY_VERSION,
        "products": n,
        "products_matched": sum(1 for r in results if r["matches"]),
        "trending_attributes": len(rising),
        "trending_attributes_matched": sum(1 for t in rising if carried[id(t)] > 0),
    }
    return results, meta

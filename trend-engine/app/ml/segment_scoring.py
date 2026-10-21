"""Scores partner-catalogue products against the rising SEGMENTS (attribute combinations). Pure: no DB, no HTTP.

A product matches a segment only when it carries BOTH parts: a white top does not match "white + dress", and a
dress that is not white does not either. One rising attribute on its own therefore earns nothing here.

contribution = segment_score x confidence_weight x part_weights x specificity
  confidence_weight  high 1.0, medium 0.6; low-confidence and falling segments are ignored
  part_weights       exact leaf 1.0, same family 0.5, multiplied across the two parts
  specificity        log(N/df)/log(N): a segment carried by most of the batch says little
segment_score of a product = the sum of its strongest TOP_MATCHES contributions.
"""
from __future__ import annotations

import math

from app.ml.product_scoring import CONFIDENCE_WEIGHT, FAMILY_WEIGHT, MIN_BATCH_FOR_SPECIFICITY, SPECIFICITY_FLOOR, _match_kind
from app.ml.taxonomy import canonical_attributes

TOP_MATCHES = 3


def _part_weight(kind: str | None) -> float:
    if kind == "exact":
        return 1.0
    if kind == "family":
        return FAMILY_WEIGHT
    return 0.0


def score_segments(products: list[dict], segments: list[dict]) -> list[dict]:
    """products: descriptors with an 'id'. segments: rows with segment_type, segment_value, part1_type,
    part1_value, part2_type, part2_value, score, confidence. Returns one result per product, in order."""
    rising = [
        s for s in segments
        if s["score"] > 0 and s.get("confidence") in CONFIDENCE_WEIGHT
    ]
    canon = [canonical_attributes(p) for p in products]
    n = len(products)

    hits: list[list[tuple[dict, float]]] = [[] for _ in products]
    carried = {id(s): 0 for s in rising}
    for i, attrs in enumerate(canon):
        for s in rising:
            w1 = _part_weight(_match_kind(s["part1_type"], s["part1_value"], attrs.get(s["part1_type"], set())))
            if not w1:
                continue
            w2 = _part_weight(_match_kind(s["part2_type"], s["part2_value"], attrs.get(s["part2_type"], set())))
            if not w2:
                continue
            hits[i].append((s, w1 * w2))
            carried[id(s)] += 1

    def specificity(segment: dict) -> float:
        df = carried[id(segment)]
        if n < MIN_BATCH_FOR_SPECIFICITY or df == 0:
            return 1.0
        return max(SPECIFICITY_FLOOR, math.log(n / df) / math.log(n))

    results = []
    for p, matched in zip(products, hits):
        contributions = []
        for s, parts_weight in matched:
            weight = CONFIDENCE_WEIGHT[s["confidence"]] * parts_weight
            contributions.append({
                "segment_type": s["segment_type"],
                "segment": s["segment_value"],
                "parts": [
                    {"attr_type": s["part1_type"], "attr_value": s["part1_value"]},
                    {"attr_type": s["part2_type"], "attr_value": s["part2_value"]},
                ],
                "match": "exact" if parts_weight == 1.0 else "family",
                "trend_score": round(float(s["score"]), 4),
                "confidence": s["confidence"],
                "contribution": round(float(s["score"]) * weight * specificity(s), 4),
            })
        contributions.sort(key=lambda c: c["contribution"], reverse=True)
        results.append({
            "id": p["id"],
            "segment_score": round(sum(c["contribution"] for c in contributions[:TOP_MATCHES]), 4),
            "segments": contributions,
        })
    return results

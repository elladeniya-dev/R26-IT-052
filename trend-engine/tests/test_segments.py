"""Segments: attribute combinations ("white + dress") and the cloth-level score built from them."""
import pandas as pd

from app.ml.segment_scoring import score_segments
from app.ml.segments import SEGMENT_TYPES, parse_segment, segment_rows


def seg(seg_type, p1, p2, score=1.0, confidence="high"):
    (t1, v1), (t2, v2) = parse_segment(seg_type, f"{p1} + {p2}")
    return {
        "segment_type": seg_type, "segment_value": f"{p1} + {p2}",
        "part1_type": t1, "part1_value": v1, "part2_type": t2, "part2_value": v2,
        "score": score, "confidence": confidence,
    }


# ---------------------------------------------------------------- building segments
def test_parse_segment_round_trips():
    assert parse_segment("color_x_category", "white + dress") == (("color", "white"), ("category", "dress"))
    assert parse_segment("category_x_sleeve_length", "dress + sleeveless") == (
        ("category", "dress"), ("sleeve_length", "sleeveless"))


def test_segment_rows_pairs_attributes_of_the_same_product_and_day_only():
    attrs = pd.DataFrame([
        ("2026-10-01", "a:1", "a", "color", "white"), ("2026-10-01", "a:1", "a", "category", "dress"),
        ("2026-10-01", "a:1", "a", "fabric", "linen"),
        ("2026-10-01", "b:2", "b", "color", "black"), ("2026-10-01", "b:2", "b", "category", "top"),
        ("2026-10-02", "a:1", "a", "color", "white"),      # no category that day: no segment
    ], columns=["date", "product_id", "brand", "attr_type", "attr"])
    rows = segment_rows(attrs)
    got = set(zip(rows.date, rows.product_id, rows.attr_type, rows.attr))
    assert ("2026-10-01", "a:1", "color_x_category", "white + dress") in got
    assert ("2026-10-01", "a:1", "fabric_x_category", "linen + dress") in got
    assert ("2026-10-01", "a:1", "color_x_fabric", "white + linen") in got
    assert ("2026-10-01", "b:2", "color_x_category", "black + top") in got
    assert not any(date == "2026-10-02" for date, *_ in got)
    assert set(rows.attr_type) <= set(SEGMENT_TYPES)


def test_segment_rows_tolerates_enum_style_type_names_and_empty_input():
    attrs = pd.DataFrame([
        ("2026-10-01", "a:1", "a", "AttrType.color", "white"), ("2026-10-01", "a:1", "a", "AttrType.category", "dress"),
    ], columns=["date", "product_id", "brand", "attr_type", "attr"])
    assert list(segment_rows(attrs).attr) == ["white + dress"]
    assert segment_rows(attrs.iloc[0:0]).empty


# ---------------------------------------------------------------- scoring a cloth
def test_a_cloth_needs_both_parts_of_a_segment():
    segments = [seg("color_x_category", "white", "dress", 2.0)]
    products = [
        {"id": "white-dress", "title": "Linen Dress", "category": "dress", "subcategory": "dress", "colors": ["white"]},
        {"id": "white-top", "title": "Cotton Top", "category": "top", "subcategory": "top", "colors": ["white"]},
        {"id": "black-dress", "title": "Midi Dress", "category": "dress", "subcategory": "dress", "colors": ["black"]},
    ]
    by_id = {r["id"]: r for r in score_segments(products, segments)}
    assert by_id["white-dress"]["segment_score"] > 0
    assert by_id["white-top"]["segment_score"] == 0      # white alone is not "white + dress"
    assert by_id["black-dress"]["segment_score"] == 0    # dress alone is not "white + dress"
    match = by_id["white-dress"]["segments"][0]
    assert match["segment"] == "white + dress" and match["match"] == "exact"
    assert [p["attr_value"] for p in match["parts"]] == ["white", "dress"]


def test_family_match_counts_half_per_part():
    segments = [seg("color_x_category", "white", "jacket", 2.0)]
    exact = {"id": "e", "title": "Jacket", "category": "jacket", "subcategory": "jacket", "colors": ["white"]}
    family = {"id": "f", "title": "Blazer", "category": "top", "subcategory": "blazer", "colors": ["white"]}
    by_id = {r["id"]: r for r in score_segments([exact, family], segments)}
    assert by_id["f"]["segment_score"] > 0
    assert round(by_id["f"]["segment_score"], 4) == round(by_id["e"]["segment_score"] * 0.5, 4)
    assert by_id["f"]["segments"][0]["match"] == "family"


def test_low_confidence_and_falling_segments_are_ignored():
    product = {"id": "p", "title": "Dress", "category": "dress", "subcategory": "dress", "colors": ["white"]}
    for s in (seg("color_x_category", "white", "dress", 2.0, "low"),
              seg("color_x_category", "white", "dress", -2.0, "high")):
        assert score_segments([product], [s])[0]["segment_score"] == 0


def test_score_sums_only_the_strongest_three_segments():
    product = {"id": "p", "title": "Linen V neck Dress", "category": "dress", "subcategory": "dress",
               "colors": ["white"], "tags": ["linen"]}
    segments = [
        seg("color_x_category", "white", "dress", 1.0), seg("fabric_x_category", "linen", "dress", 2.0),
        seg("color_x_fabric", "white", "linen", 3.0), seg("category_x_neckline", "dress", "v neck", 4.0),
    ]
    result = score_segments([product], segments)[0]
    contributions = sorted((m["contribution"] for m in result["segments"]), reverse=True)
    assert len(contributions) >= 4
    assert result["segment_score"] == round(sum(contributions[:3]), 4)


# ---------------------------------------------------------------- API
def test_segments_endpoint_shape_and_validation(client):
    r = client.get("/api/v1/trends/segments?limit=5")
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        body = r.json()
        rows = body["data"]
        assert len(rows) <= 5 and body["meta"]["count"] == len(rows)
        scores = [x["score"] for x in rows]
        assert scores == sorted(scores, reverse=True)
        for row in rows:
            assert row["segment_type"] in SEGMENT_TYPES and len(row["parts"]) == 2
            assert row["segment"] == " + ".join(p["attr_value"] for p in row["parts"])
    for bad in ("horizon=4", "limit=0", "limit=101", "min_confidence=banana"):
        assert client.get(f"/api/v1/trends/segments?{bad}").status_code == 422, bad


def test_segments_endpoint_is_not_swallowed_by_the_attribute_route(client):
    # /trends/{attr_type} would answer 422 for an unknown type; "segments" must reach its own route.
    assert client.get("/api/v1/trends/segments").status_code != 422


def test_score_products_reports_segment_fields(client):
    r = client.post("/api/v1/trends/score-products", json={"products": [
        {"id": "x", "title": "White Linen Dress", "category": "dress", "subcategory": "dress", "colors": ["white"]},
    ]})
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        item = r.json()["data"][0]
        assert "segment_score" in item and "segments" in item
        assert "trend_score" in item and "matches" in item          # the single-attribute view is unchanged
        assert "segments_tracked" in r.json()["meta"]

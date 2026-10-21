"""Vocabulary contract + scoring rules for partner-catalogue products.

The fixture is a frozen sample of a real partner catalogue (Koji). If a mapping change breaks one of
these tests, the shared vocabulary changed: review it and bump TAXONOMY_VERSION."""
import json
from pathlib import Path

import pytest

from app.ml.product_scoring import score_products
from app.ml.taxonomy import canonical_attributes, family_of

SAMPLE = json.loads((Path(__file__).parent / "fixtures" / "koji_sample.json").read_text(encoding="utf-8"))


def descriptor(p: dict) -> dict:
    return {"id": p["item_id"], "title": p["title"], "description": p["description"],
            "category": p["category"], "subcategory": p["subcategory"], "colors": p["color"], "tags": p["style"]}


def trend(attr_type, value, score=1.0, confidence="high"):
    return {"attr_type": attr_type, "attr_value": value, "score": score, "confidence": confidence}


# ---------------------------------------------------------------- vocabulary contract
@pytest.mark.parametrize("raw,expected", [
    ({"category": "pants", "subcategory": "joggers"}, "trousers"),
    ({"category": "pants", "subcategory": "pants"}, "trousers"),
    ({"category": "jeans", "subcategory": "jeans"}, "trousers"),
    ({"category": "jumpsuit", "subcategory": "jumpsuit"}, "jumpsuit/playsuit"),
    ({"category": "set", "subcategory": "two_piece_set"}, "garment set"),
    ({"category": "top", "subcategory": "crop_top"}, "top"),
    ({"category": "leggings", "subcategory": "leggings"}, "leggings/tights"),
])
def test_partner_categories_map_to_canonical_values(raw, expected):
    assert canonical_attributes(raw)["category"] == {expected}


def test_every_sample_product_gets_a_canonical_category():
    missing = [p["title"] for p in SAMPLE if not canonical_attributes(descriptor(p)).get("category")]
    assert not missing, f"no canonical category for: {missing}"


def test_length_words_only_apply_to_garments_they_describe():
    assert "garment_length" not in canonical_attributes({"title": "AirSculpt Midi 6 Short", "category": "shorts"})
    assert canonical_attributes({"title": "Quinn Midi Dress", "category": "dress"})["garment_length"] == {"midi"}
    assert canonical_attributes({"title": "Cropped Knit Top", "category": "top"})["garment_length"] == {"cropped"}


def test_colors_collapse_to_canonical_shades_and_junk_is_dropped():
    attrs = canonical_attributes({"colors": ["Jet Black", "off-white", "multi", "unknown"]})
    assert attrs["color"] == {"black", "off white"}


def test_families_group_close_substitutes_only():
    assert family_of("category", "blazer") == family_of("category", "jacket") == "outerwear"
    assert family_of("category", "top") is None  # a rising "blouse" must not boost every top
    assert family_of("category", "blouse") == family_of("category", "shirt") == "shirting"
    assert family_of("color", "off white") == family_of("color", "white")
    assert family_of("color", "burgundy") is None and family_of("color", "red") is None  # distinct fashion colours
    assert family_of("fabric", "cotton") is None


# ---------------------------------------------------------------- scoring rules
def test_exact_match_outscores_family_match():
    products = [
        {"id": "blazer", "title": "Blazer", "category": "top", "subcategory": "blazer"},
        {"id": "jacket", "title": "Jacket", "category": "top", "subcategory": "jacket"},
    ]
    results, _ = score_products(products, [trend("category", "jacket", 1.0)])
    scores = {r["id"]: r["trend_score"] for r in results}
    assert scores["jacket"] > scores["blazer"] > 0
    assert {m["match"] for r in results for m in r["matches"]} == {"exact", "family"}


def test_low_confidence_and_falling_trends_are_ignored():
    products = [{"id": "d", "title": "Dress", "category": "dress", "subcategory": "dress"}]
    results, meta = score_products(products, [trend("category", "dress", 2.0, "low"), trend("category", "dress", -2.0, "high")])
    assert results[0]["trend_score"] == 0 and results[0]["matches"] == []
    assert meta["trending_attributes"] == 0


def test_generic_attributes_are_discounted_against_specific_ones():
    products = [{"id": f"t{i}", "title": "Top", "category": "top", "subcategory": "top"} for i in range(19)]
    products.append({"id": "j", "title": "Jumpsuit", "category": "jumpsuit", "subcategory": "jumpsuit"})
    results, _ = score_products(products, [trend("category", "top", 1.0), trend("category", "jumpsuit/playsuit", 1.0)])
    by_id = {r["id"]: r["trend_score"] for r in results}
    assert by_id["j"] > by_id["t0"]  # one jumpsuit in twenty says more than a top that everyone has


def test_score_sums_only_the_strongest_three_matches():
    p = [{"id": "x", "title": "Floral Midi Dress v-neck", "category": "dress", "subcategory": "dress", "colors": ["beige"], "tags": ["floral"]}]
    trends = [trend("category", "dress", 1.0), trend("color", "beige", 1.0), trend("pattern", "floral", 1.0),
              trend("garment_length", "midi", 1.0), trend("neckline", "v-neck", 1.0)]
    results, _ = score_products(p, trends)
    contributions = sorted((m["contribution"] for m in results[0]["matches"]), reverse=True)
    assert len(contributions) == 5
    assert results[0]["trend_score"] == round(sum(contributions[:3]), 4)


def test_meta_reports_coverage():
    products = [{"id": "d", "title": "Dress", "category": "dress", "subcategory": "dress"}]
    _, meta = score_products(products, [trend("category", "dress"), trend("fabric", "leather")])
    assert meta["trending_attributes"] == 2 and meta["trending_attributes_matched"] == 1
    assert meta["products"] == 1 and meta["products_matched"] == 1


def test_pants_filed_as_blazer_do_not_earn_the_jacket_trend():
    pant = {"id": "p", "title": "Flared Leg Formal Pant- Pastel Pink", "category": "top", "subcategory": "blazer"}
    assert canonical_attributes(pant)["category"] == {"trousers"}
    results, _ = score_products([pant], [trend("category", "jacket", 1.0)])
    assert results[0]["trend_score"] == 0


def test_blazer_filed_as_a_generic_top_still_earns_the_jacket_trend():
    blazer = {"id": "b", "title": "Basic Blazer - 080626", "category": "top", "subcategory": "top"}
    assert canonical_attributes(blazer)["category"] == {"blazer"}
    results, _ = score_products([blazer], [trend("category", "jacket", 1.0)])
    assert results[0]["trend_score"] > 0


def test_title_override_leaves_ambiguous_and_whole_word_cases_alone():
    assert canonical_attributes({"title": "Short Sleeve Blazer", "category": "top", "subcategory": "top"})["category"] == {"blazer"}
    assert canonical_attributes({"title": "Linen Pant Set", "category": "dress", "subcategory": "set"})["category"] == {"garment set"}
    assert canonical_attributes({"title": "Denim Jean Jacket", "category": "outerwear", "subcategory": "jacket"})["category"] == {"jacket"}
    assert canonical_attributes({"title": "Pantone Colour Tee", "category": "top", "subcategory": "top"})["category"] == {"top"}

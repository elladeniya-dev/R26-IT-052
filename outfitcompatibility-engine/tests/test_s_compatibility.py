from pathlib import Path
import sys


SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from app.s_compatibility import calculate_compatibility_score


def test_calculate_compatibility_score_for_casual_outfit():
    sample_outfit = [
        {
            "item_id": "P001",
            "title": "Black Casual Crop Top",
            "category": "top",
            "color": ["black"],
            "style": ["casual"],
        },
        {
            "item_id": "P002",
            "title": "Blue Denim Jeans",
            "category": "bottom",
            "color": ["blue"],
            "style": ["casual"],
        },
        {
            "item_id": "P003",
            "title": "White Casual Jacket",
            "category": "outerwear",
            "color": ["white"],
            "style": ["casual"],
        },
    ]

    result = calculate_compatibility_score(
        outfit_items=sample_outfit,
        occasion="casual",
    )

    assert result["compatibility_score"] == 1.0
    assert "categories form a complete outfit" in result["reason_tags"]


def test_style_conflict_scores_lower_than_matching_style():
    matching_outfit = [
        {
            "item_id": "P001",
            "title": "Black Casual Top",
            "category": "top",
            "color": ["black"],
            "style": ["casual"],
        },
        {
            "item_id": "P002",
            "title": "Blue Casual Jeans",
            "category": "bottom",
            "color": ["blue"],
            "style": ["casual"],
        },
    ]
    conflicting_outfit = [
        {
            "item_id": "P001",
            "title": "Black Casual Top",
            "category": "top",
            "color": ["black"],
            "style": ["casual"],
        },
        {
            "item_id": "P009",
            "title": "Grey Formal Trousers",
            "category": "bottom",
            "color": ["grey"],
            "style": ["formal"],
        },
    ]

    matching_result = calculate_compatibility_score(
        outfit_items=matching_outfit,
        occasion="casual",
    )
    conflicting_result = calculate_compatibility_score(
        outfit_items=conflicting_outfit,
        occasion="formal",
    )

    assert matching_result["compatibility_score"] > conflicting_result["compatibility_score"]
    assert "style conflict detected" in conflicting_result["reason_tags"]


def test_duplicate_main_category_is_penalized():
    duplicate_top_outfit = [
        {
            "item_id": "P001",
            "title": "Black Casual Top",
            "category": "top",
            "color": ["black"],
            "style": ["casual"],
        },
        {
            "item_id": "P010",
            "title": "White Formal Shirt",
            "category": "top",
            "color": ["white"],
            "style": ["formal"],
        },
    ]

    result = calculate_compatibility_score(
        outfit_items=duplicate_top_outfit,
        occasion="casual",
    )

    assert result["score_breakdown"]["category_match_score"] == 0.5
    assert "duplicate main clothing category found" in result["reason_tags"]


if __name__ == "__main__":
    test_calculate_compatibility_score_for_casual_outfit()
    test_style_conflict_scores_lower_than_matching_style()
    test_duplicate_main_category_is_penalized()
    print("Compatibility test passed.")

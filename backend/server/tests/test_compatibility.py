from pathlib import Path
import sys


SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from app.compatibility import calculate_compatibility_score


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


if __name__ == "__main__":
    test_calculate_compatibility_score_for_casual_outfit()
    print("Compatibility test passed.")

from pathlib import Path
import os
import sys
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.s_database import Base
from app.s_models import Product
from app.s_outfit_generator import generate_outfits_for_selected_item


def create_test_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def add_product(
    db,
    item_id,
    title,
    category,
    color,
    style,
    price=1000,
    availability=True,
):
    db.add(
        Product(
            item_id=item_id,
            title=title,
            category=category,
            subcategory=category,
            color=color,
            style=style,
            brand="Test Brand",
            price=price,
            currency="LKR",
            image_url=f"https://gflock.lk/cdn/shop/files/{item_id}.jpg",
            product_url=f"https://gflock.lk/products/{item_id}",
            source="gflock",
            description=title,
            availability=availability,
        )
    )


def test_generate_outfits_ranks_best_style_match_first():
    db = create_test_session()

    try:
        add_product(db, "P001", "Black Casual Top", "top", ["black"], ["casual"], 3000)
        add_product(db, "P002", "Blue Casual Jeans", "bottom", ["blue"], ["casual"], 4500)
        add_product(db, "P003", "Beige Formal Trousers", "bottom", ["beige"], ["formal"], 5000)
        db.commit()

        with patch("app.s_outfit_generator.calculate_outfit_ml_score", return_value=0.5):
            result = generate_outfits_for_selected_item(
                db=db,
                user_id="USR001",
                selected_item_id="P001",
                occasion="casual",
                max_outfits=2,
                max_items_per_category=5,
            )

        assert result["success"] is True
        assert len(result["outfits"]) == 2
        assert result["outfits"][0]["items"][1]["item_id"] == "P002"
        assert result["outfits"][0]["compatibility_score"] >= result["outfits"][1]["compatibility_score"]
        assert result["outfits"][0]["outfit_id"] == "OUT001"

    finally:
        db.close()


def test_generate_outfits_applies_preferred_color_filter():
    db = create_test_session()

    try:
        add_product(db, "P001", "White Formal Shirt", "top", ["white"], ["formal", "office"], 3000)
        add_product(db, "P002", "Black Formal Trousers", "bottom", ["black"], ["formal", "office"], 4500)
        add_product(db, "P003", "Blue Casual Jeans", "bottom", ["blue"], ["casual"], 5000)
        db.commit()

        with patch("app.s_outfit_generator.calculate_outfit_ml_score", return_value=0.5):
            result = generate_outfits_for_selected_item(
                db=db,
                user_id="USR001",
                selected_item_id="P001",
                occasion="office",
                max_outfits=3,
                preferred_colors=["black"],
                max_items_per_category=5,
            )

        assert result["success"] is True
        assert len(result["outfits"]) == 2
        assert result["outfits"][0]["items"][1]["item_id"] == "P002"
        assert result["outfits"][0]["applied_filters"]["preferred_colors"] == ["black"]

    finally:
        db.close()


def test_generate_outfits_treats_skirt_as_bottom_category():
    db = create_test_session()

    try:
        add_product(db, "P001", "Black Skirt", "skirt", ["black"], ["casual"], 3000)
        add_product(db, "P002", "White Casual Top", "top", ["white"], ["casual"], 4500)
        db.commit()

        with patch("app.s_outfit_generator.calculate_outfit_ml_score", return_value=0.5):
            result = generate_outfits_for_selected_item(
                db=db,
                user_id="USR001",
                selected_item_id="P001",
                occasion="casual",
                max_outfits=1,
                max_items_per_category=5,
            )

        assert result["success"] is True
        assert result["outfits"][0]["items"][0]["role"] == "bottom"
        assert result["outfits"][0]["items"][1]["item_id"] == "P002"

    finally:
        db.close()


def test_generate_outfits_falls_back_when_preferred_colors_do_not_match():
    db = create_test_session()

    try:
        add_product(db, "P001", "Black Skirt", "skirt", ["black"], ["casual"], 3000)
        add_product(db, "P002", "Unknown Color Top", "top", ["unknown"], ["casual"], 4500)
        db.commit()

        with patch("app.s_outfit_generator.calculate_outfit_ml_score", return_value=0.5):
            result = generate_outfits_for_selected_item(
                db=db,
                user_id="USR001",
                selected_item_id="P001",
                occasion="casual",
                max_outfits=1,
                preferred_colors=["white", "blue"],
                max_items_per_category=5,
            )

        assert result["success"] is True
        assert result["outfits"][0]["items"][1]["item_id"] == "P002"

    finally:
        db.close()


def test_generate_outfits_honors_requested_outfit_count_when_fetch_limit_is_lower():
    db = create_test_session()

    try:
        add_product(db, "P001", "Black Skirt", "skirt", ["black"], ["casual"], 3000)

        for index in range(5):
            add_product(
                db,
                f"P10{index}",
                f"Casual Top {index}",
                "top",
                ["white"],
                ["casual"],
                4000 + index,
            )

        db.commit()

        with patch("app.s_outfit_generator.calculate_outfit_ml_score", return_value=0.5):
            result = generate_outfits_for_selected_item(
                db=db,
                user_id="USR001",
                selected_item_id="P001",
                occasion="casual",
                max_outfits=5,
                max_items_per_category=2,
            )

        assert result["success"] is True
        assert len(result["outfits"]) == 5

    finally:
        db.close()


def test_generate_outfits_prioritizes_different_matching_main_items():
    db = create_test_session()

    try:
        add_product(db, "P001", "Black Skirt", "skirt", ["black"], ["casual"], 3000)

        for index, color in enumerate(["white", "blue", "green", "red", "beige"]):
            add_product(
                db,
                f"P20{index}",
                f"{color.title()} Casual Shirt",
                "top",
                [color],
                ["casual"],
                4000 + index,
            )

        add_product(db, "P301", "White Heel", "footwear", ["white"], ["casual"], 5000)
        add_product(db, "P302", "Black Heel", "footwear", ["black"], ["casual"], 5000)
        db.commit()

        with patch("app.s_outfit_generator.calculate_outfit_ml_score", return_value=0.5):
            result = generate_outfits_for_selected_item(
                db=db,
                user_id="USR001",
                selected_item_id="P001",
                occasion="casual",
                max_outfits=5,
                max_items_per_category=5,
            )

        top_item_ids = [
            item["item_id"]
            for outfit in result["outfits"]
            for item in outfit["items"]
            if item["role"] == "top"
        ]

        assert result["success"] is True
        assert len(result["outfits"]) == 5
        assert len(set(top_item_ids)) == 5

    finally:
        db.close()


if __name__ == "__main__":
    test_generate_outfits_ranks_best_style_match_first()
    test_generate_outfits_applies_preferred_color_filter()
    test_generate_outfits_treats_skirt_as_bottom_category()
    test_generate_outfits_falls_back_when_preferred_colors_do_not_match()
    test_generate_outfits_honors_requested_outfit_count_when_fetch_limit_is_lower()
    test_generate_outfits_prioritizes_different_matching_main_items()
    print("Outfit generator tests passed.")

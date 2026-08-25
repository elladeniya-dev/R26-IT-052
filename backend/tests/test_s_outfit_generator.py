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
            image_url=f"https://example.com/{item_id}.jpg",
            product_url=f"https://example.com/{item_id}",
            source="test",
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
        assert len(result["outfits"]) == 1
        assert result["outfits"][0]["items"][1]["item_id"] == "P002"
        assert result["outfits"][0]["applied_filters"]["preferred_colors"] == ["black"]

    finally:
        db.close()


if __name__ == "__main__":
    test_generate_outfits_ranks_best_style_match_first()
    test_generate_outfits_applies_preferred_color_filter()
    print("Outfit generator tests passed.")

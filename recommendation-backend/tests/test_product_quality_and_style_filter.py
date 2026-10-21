import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.schemas.recommendation_schema import RecommendationRequest
from app.services.fashion_attribute_normalizer import canonicalize_attribute
from app.services.product_quality_service import is_non_fashion_product
from app.services.recommendation_service import generate_recommendations


class FakeQuery:
    def __init__(self, products):
        self.products = products

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.products


class FakeDatabase:
    def __init__(self, products):
        self.products = products

    def query(self, model):
        return FakeQuery(self.products)


def product(item_id, title, styles, score=0.8):
    return SimpleNamespace(
        item_id=item_id,
        title=title,
        category="top",
        subcategory="tshirt",
        color=["pink"],
        style=styles,
        brand="zigzag",
        source="zigzag",
        price=score * 1000,
        image_url=f"https://shop.test/{item_id}.jpg",
        product_url=f"https://shop.test/{item_id}",
        description="A real clothing product",
        availability=True,
    )


def request(style_filter, max_results=5):
    return RecommendationRequest(
        user_id="test",
        preferred_categories=["top"],
        preferred_colors=[],
        preferred_styles=[],
        preferred_brands=[],
        style_filter=style_filter,
        max_results=max_results,
    )


def fake_score(current_product, current_request):
    score = current_product.price / 1000
    return score, 1.0, 0.0, 1.0, ["test match"]


class ProductQualityAndStyleFilterTests(unittest.TestCase):
    def test_known_gift_card_and_voucher_phrases_are_rejected(self):
        for title in ("Bellini Gift Card", "Gift-Card", "E-Gift Card", "Gift Voucher"):
            with self.subTest(title=title):
                self.assertTrue(is_non_fashion_product({"title": title}))

    def test_generic_gift_word_does_not_reject_clothing(self):
        self.assertFalse(is_non_fashion_product({"title": "Gift Collection Dress"}))

    @patch("app.services.recommendation_service.calculate_recommendation_score", fake_score)
    def test_legacy_gift_card_is_excluded_from_candidates(self):
        legacy = product("gift", "Bellini Gift Card", ["formal"], 1.0)
        valid = product("dress", "Formal Midi Dress", ["formal"], 0.8)
        results = generate_recommendations(FakeDatabase([legacy, valid]), request("formal"))
        self.assertEqual([item["item_id"] for item in results], ["dress"])

    @patch("app.services.recommendation_service.calculate_recommendation_score", fake_score)
    def test_formal_exact_filter_excludes_smart_casual_tshirt(self):
        tshirt = product("tee", "Hot Pink Oversized T-shirt", "casual, smart_casual, trendy")
        results = generate_recommendations(FakeDatabase([tshirt]), request("Formal"))
        self.assertEqual(results, [])

    @patch("app.services.recommendation_service.calculate_recommendation_score", fake_score)
    def test_formal_exact_filter_includes_formal_token(self):
        dress = product("dress", "Formal Dress", "formal,elegant")
        results = generate_recommendations(FakeDatabase([dress]), request("Formal"))
        self.assertEqual([item["item_id"] for item in results], ["dress"])

    @patch("app.services.recommendation_service.calculate_recommendation_score", fake_score)
    def test_all_has_no_hard_style_exclusion(self):
        casual = product("casual", "Casual Top", ["casual"])
        formal = product("formal", "Formal Top", ["formal"])
        results = generate_recommendations(FakeDatabase([casual, formal]), request("All"))
        self.assertEqual({item["item_id"] for item in results}, {"casual", "formal"})

    def test_party_wear_filter_aliases_are_identical(self):
        self.assertEqual(
            canonicalize_attribute("Party Wear", "style"),
            canonicalize_attribute("party_wear", "style"),
        )

    @patch("app.services.recommendation_service.calculate_recommendation_score", fake_score)
    def test_style_filter_is_applied_before_top_n(self):
        casual_products = [
            product(f"casual-{index}", f"Casual {index}", ["casual"], 1.0 - index / 100)
            for index in range(5)
        ]
        lower_ranked_formal = product("formal", "Formal Dress", ["formal"], 0.5)
        results = generate_recommendations(
            FakeDatabase(casual_products + [lower_ranked_formal]),
            request("formal", max_results=1),
        )
        self.assertEqual([item["item_id"] for item in results], ["formal"])


if __name__ == "__main__":
    unittest.main()

import unittest
from types import SimpleNamespace

from app.schemas.recommendation_schema import RecommendationRequest
from app.services.preference_weighting_service import (
    prioritize_explicit_category_candidates,
)
from app.services.recommendation_service import (
    calculate_user_match_score,
    diversify_recommendations,
)


class RecommendationWeightedScoringTests(unittest.TestCase):
    def test_actual_user_match_score_prefers_explicit_category(self):
        request = RecommendationRequest(
            user_id=20,
            preferred_categories=["Tops", "Jeans"],
            preferred_colors=[],
            preferred_styles=[],
            preferred_brands=[],
            category_weights={"Tops": 1.0, "Jeans": 0.55},
        )

        def product(category):
            return SimpleNamespace(
                category=category,
                color=[],
                style=[],
                brand=None,
                price=None,
            )

        explicit_score, _ = calculate_user_match_score(product("Tops"), request)
        inferred_score, _ = calculate_user_match_score(product("Jeans"), request)

        self.assertEqual(explicit_score, 1.0)
        self.assertEqual(inferred_score, 0.55)

    def test_safeguard_then_diversification_keeps_representation_and_variety(self):
        categories = [
            "Jeans", "Blazers", "Jeans", "Blazers", "Tops", "Shirts",
            "Tops", "Jeans", "Shirts", "Blazers", "Tops", "Shirts",
        ]
        products = [
            {
                "item_id": str(index),
                "category": category,
                "final_score": 1 - index / 100,
                "source": f"source-{index % 4}",
                "brand": f"brand-{index % 4}",
                "title": f"product-{index}",
            }
            for index, category in enumerate(categories)
        ]

        prioritized = prioritize_explicit_category_candidates(
            products,
            explicit_categories=["Tops", "Shirts"],
            max_results=10,
        )
        final = diversify_recommendations(prioritized, max_results=10)
        explicit_count = sum(
            item["category"] in {"Tops", "Shirts"} for item in final
        )

        self.assertGreaterEqual(explicit_count, 4)
        self.assertTrue(any(
            item["category"] in {"Jeans", "Blazers"} for item in final
        ))
        self.assertEqual(len({item["item_id"] for item in final}), len(final))


if __name__ == "__main__":
    unittest.main()

import unittest

from app.services.preference_weighting_service import (
    get_explicit_categories,
    matched_preference_confidence,
    normalize_chala_preference_payload,
    prioritize_explicit_category_candidates,
)


class PreferenceWeightingServiceTests(unittest.TestCase):
    def test_weighted_category_contribution_prefers_explicit(self):
        weights = {"Tops": 1.0, "Jeans": 0.55}
        explicit_confidence = matched_preference_confidence(
            "Tops", ["Tops", "Jeans"], weights
        )
        inferred_confidence = matched_preference_confidence(
            "Jeans", ["Tops", "Jeans"], weights
        )

        self.assertEqual(0.30 * explicit_confidence, 0.30)
        self.assertAlmostEqual(0.30 * inferred_confidence, 0.165)

    def test_legacy_payload_and_missing_weight_use_flat_behavior(self):
        payload = normalize_chala_preference_payload(
            {"categories": ["Tops", "Jeans"]},
            user_id=20,
        )

        self.assertEqual(payload["category_weights"], {})
        self.assertEqual(payload["colors"], [])
        self.assertEqual(
            matched_preference_confidence(
                "Jeans", payload["categories"], payload["category_weights"]
            ),
            1.0,
        )

    def test_explicit_category_safeguard_represents_and_interleaves(self):
        categories = [
            "Jeans",
            "Blazers",
            "Jeans",
            "Blazers",
            "Tops",
            "Shirts",
            "Tops",
            "Jeans",
            "Shirts",
            "Blazers",
            "Tops",
            "Shirts",
        ]
        products = [
            {"item_id": str(index), "category": category, "final_score": 1 - index / 100}
            for index, category in enumerate(categories)
        ]

        prioritized = prioritize_explicit_category_candidates(
            products,
            explicit_categories=["Tops", "Shirts"],
            max_results=10,
        )
        top_ten_categories = [item["category"] for item in prioritized[:10]]
        explicit_count = sum(
            category in {"Tops", "Shirts"} for category in top_ten_categories
        )

        self.assertGreaterEqual(explicit_count, 4)
        self.assertTrue(any(
            category in {"Jeans", "Blazers"} for category in top_ten_categories
        ))
        self.assertEqual(len({item["item_id"] for item in prioritized}), len(products))

    def test_explicit_categories_come_only_from_source_metadata(self):
        sources = {
            "categories": {
                "Tops": ["explicit"],
                "Jeans": ["ml_expansion", "learned"],
            }
        }

        self.assertEqual(get_explicit_categories(sources), ["Tops"])

    def test_null_payload_is_safe(self):
        payload = normalize_chala_preference_payload(None, user_id=20)

        self.assertEqual(payload["categories"], [])
        self.assertEqual(payload["preference_sources"], {})


if __name__ == "__main__":
    unittest.main()

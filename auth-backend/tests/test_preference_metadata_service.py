import unittest

from app.services.preference_metadata_service import (
    build_weighted_preference_metadata,
)


class PreferenceMetadataServiceTests(unittest.TestCase):
    def build_metadata(self, learned=None, expansions=None):
        return build_weighted_preference_metadata(
            flat_preferences={
                "categories": ["Tops", "Shirts", "Jeans", "Blazers"],
                "colors": None,
                "styles": [],
                "occasions": [],
                "preferred_brands": [],
            },
            explicit_preferences={
                "categories": ["Tops", "Shirts"],
                "colors": [],
                "styles": [],
                "occasions": [],
                "preferred_brands": [],
            },
            learned_weights=learned or {},
            ml_expansions=expansions or {
                "categories": [
                    {"preference": "Jeans", "probability": 0.55},
                    {"preference": "Blazers", "probability": 0.42},
                ]
            },
        )

    def test_explicit_preferences_outrank_ml_expansions(self):
        metadata = self.build_metadata()

        self.assertEqual(metadata["category_weights"]["top"], 1.0)
        self.assertEqual(metadata["category_weights"]["shirt"], 1.0)
        self.assertEqual(metadata["category_weights"]["jeans"], 0.55)
        self.assertEqual(metadata["category_weights"]["blazer"], 0.42)

    def test_duplicate_sources_use_strongest_confidence_case_insensitively(self):
        metadata = build_weighted_preference_metadata(
            flat_preferences={"categories": ["Jeans"]},
            explicit_preferences={"categories": ["jeans"]},
            learned_weights={"category_weights": {"JEANS": 0.8}},
            ml_expansions={
                "categories": [{"preference": "Jeans", "probability": 0.55}]
            },
        )

        self.assertEqual(metadata["category_weights"], {"jeans": 1.0})
        self.assertEqual(
            metadata["preference_sources"]["categories"]["jeans"],
            ["explicit", "learned", "ml_expansion"],
        )

    def test_learned_evidence_can_raise_an_inferred_preference(self):
        metadata = self.build_metadata(
            learned={"category_weights": {"Jeans": 0.9}}
        )

        self.assertEqual(metadata["category_weights"]["jeans"], 0.9)
        self.assertEqual(
            metadata["preference_sources"]["categories"]["jeans"],
            ["learned", "ml_expansion"],
        )

    def test_null_and_missing_dimensions_are_safe(self):
        metadata = build_weighted_preference_metadata(None, None, None, None)

        self.assertEqual(metadata["category_weights"], {})
        self.assertEqual(metadata["preference_sources"]["colors"], {})

    def test_color_case_duplicates_merge_to_strongest_weight_and_sources(self):
        metadata = build_weighted_preference_metadata(
            flat_preferences={"colors": ["Blue", "BLUE"]},
            explicit_preferences={"colors": ["blue"]},
            learned_weights={"color_weights": {"blue": 0.5, "Blue": 0.8}},
            ml_expansions={"colors": [{"preference": "BLUE", "probability": 0.4}]},
        )

        self.assertEqual(metadata["color_weights"], {"blue": 1.0})
        self.assertEqual(
            metadata["preference_sources"]["colors"]["blue"],
            ["explicit", "learned", "ml_expansion"],
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from app.services.fashion_attribute_normalizer import (
    canonicalize_values,
    canonicalize_weight_map,
)
from app.schemas import OnboardingRequest


class FashionAttributeNormalizerTests(unittest.TestCase):
    def test_color_case_variants_have_one_canonical_value(self):
        self.assertEqual(canonicalize_values(["Blue", "blue", "BLUE"], "color"), ["blue"])

    def test_duplicate_weights_use_maximum(self):
        self.assertEqual(
            canonicalize_weight_map({"blue": 1.0, "Blue": 0.5}, "color"),
            {"blue": 1.0},
        )

    def test_category_aliases_do_not_create_duplicate_tops(self):
        self.assertEqual(canonicalize_values(["top", "Tops"], "category"), ["top"])

    def test_style_separator_variants_are_equivalent(self):
        self.assertEqual(
            canonicalize_values(
                ["Smart Casual", "smart_casual", "smart-casual"], "style"
            ),
            ["smart_casual"],
        )

    def test_onboarding_future_write_is_canonicalized(self):
        request = OnboardingRequest(
            preferred_categories=["Tops", "top"],
            preferred_colors=["Blue", "BLUE"],
            preferred_styles=["Party Wear", "party_wear"],
            occasions=["Office / Work"],
            preferred_brands=["Bellini"],
        )

        self.assertEqual(request.preferred_categories, ["top"])
        self.assertEqual(request.preferred_colors, ["blue"])
        self.assertEqual(request.preferred_styles, ["party"])


if __name__ == "__main__":
    unittest.main()

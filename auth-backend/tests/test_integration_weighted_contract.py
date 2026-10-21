import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.models import User, UserLearnedPreference, UserOnboardingPreference
from app.routes.integration_routes import (
    get_user_enriched_preferences_for_integration,
)


class FakeQuery:
    def __init__(self, value):
        self.value = value

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.value


class FakeDatabase:
    def __init__(self, values):
        self.values = values

    def query(self, model):
        return FakeQuery(self.values.get(model))


class IntegrationWeightedContractTests(unittest.TestCase):
    def test_route_keeps_flat_lists_and_adds_weighted_sources(self):
        user = SimpleNamespace(user_id=20)
        onboarding = SimpleNamespace(
            preferred_categories=["Tops", "Shirts"],
            preferred_colors=[],
            preferred_styles=[],
            occasions=[],
            preferred_brands=[],
        )
        learned = SimpleNamespace(
            category_weights={"Jeans": 0.8},
            color_weights={},
            style_weights={},
            brand_weights={},
            occasion_weights={},
        )
        database = FakeDatabase(
            {
                User: user,
                UserOnboardingPreference: onboarding,
                UserLearnedPreference: learned,
            }
        )
        enriched_result = {
            "enriched_preferences": {
                "preferred_categories": ["Tops", "Shirts", "Jeans", "Blazers"],
                "preferred_colors": [],
                "preferred_styles": [],
                "occasions": [],
                "preferred_brands": [],
            },
            "ml_expansions": {
                "categories": [
                    {"preference": "Jeans", "probability": 0.55},
                    {"preference": "Blazers", "probability": 0.42},
                ]
            },
        }

        with patch(
            "app.routes.integration_routes.get_enriched_current_preferences",
            return_value=enriched_result,
        ):
            response = get_user_enriched_preferences_for_integration(
                user_id=20,
                db=database,
            )

        self.assertEqual(
            response["categories"],
            ["top", "shirt", "jeans", "blazer"],
        )
        self.assertEqual(response["category_weights"]["top"], 1.0)
        self.assertEqual(response["category_weights"]["jeans"], 0.8)
        self.assertEqual(
            response["preference_sources"]["categories"]["jeans"],
            ["learned", "ml_expansion"],
        )


if __name__ == "__main__":
    unittest.main()

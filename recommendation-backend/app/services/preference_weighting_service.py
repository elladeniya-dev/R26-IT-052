"""Pure helpers for confidence-weighted preference matching and ranking."""

import math
from typing import Any

from app.services.fashion_attribute_normalizer import (
    canonicalize_attribute,
    canonicalize_values,
    canonicalize_weight_map,
)


EXPLICIT_CATEGORY_TARGET_RATIO = 0.40


def normalize_text_list(values, dimension: str | None = None):
    return canonicalize_values(values, dimension)


def normalize_weight_map(weights, dimension: str | None = None) -> dict[str, float]:
    return canonicalize_weight_map(weights, dimension)


def matched_preference_confidence(
    product_values,
    preferred_values,
    preference_weights,
    dimension: str | None = None,
) -> float | None:
    """
    Return the strongest confidence among matching preferences.

    A missing value in a missing/partial weight map deliberately falls back to
    1.0, reproducing Koji's pre-contract flat-list behavior.
    """

    product_value_set = set(normalize_text_list(product_values, dimension))
    preferred_value_set = set(normalize_text_list(preferred_values, dimension))
    matching_values = product_value_set & preferred_value_set

    if not matching_values:
        return None

    normalized_weights = normalize_weight_map(preference_weights, dimension)
    return max(normalized_weights.get(value, 1.0) for value in matching_values)


def get_explicit_categories(preference_sources) -> list[str]:
    if not isinstance(preference_sources, dict):
        return []

    category_sources = preference_sources.get("categories", {})
    if not isinstance(category_sources, dict):
        return []

    explicit_categories = []
    for category, sources in category_sources.items():
        if "explicit" in normalize_text_list(sources):
            explicit_categories.append(str(category))

    return explicit_categories


def product_matches_explicit_category(item: dict, explicit_categories) -> bool:
    category = item.get("category")
    if not category:
        return False

    return canonicalize_attribute(category, "category") in set(
        normalize_text_list(explicit_categories, "category")
    )


def prioritize_explicit_category_candidates(
    scored_products: list[dict],
    explicit_categories,
    max_results: int,
    target_ratio: float = EXPLICIT_CATEGORY_TARGET_RATIO,
) -> list[dict]:
    """
    Stably interleave explicit-category candidates near the top of the ranking.

    Only the prefix that can affect Top-N is adjusted. Relative score order is
    preserved within explicit and non-explicit groups, and the untouched
    remainder is appended for the normal diversification pass.
    """

    if not scored_products or not explicit_categories or max_results <= 0:
        return scored_products

    target_ratio = max(0.0, min(1.0, float(target_ratio)))
    explicit_candidates = [
        item
        for item in scored_products
        if product_matches_explicit_category(item, explicit_categories)
    ]
    other_candidates = [
        item
        for item in scored_products
        if not product_matches_explicit_category(item, explicit_categories)
    ]

    target_count = min(
        len(explicit_candidates),
        math.ceil(max_results * target_ratio),
    )
    if target_count == 0:
        return scored_products

    prioritized_prefix = []
    explicit_index = 0
    other_index = 0

    for position in range(max_results):
        desired_explicit_so_far = min(
            target_count,
            math.ceil((position + 1) * target_ratio),
        )

        if (
            explicit_index < len(explicit_candidates)
            and explicit_index < desired_explicit_so_far
        ):
            prioritized_prefix.append(explicit_candidates[explicit_index])
            explicit_index += 1
        elif other_index < len(other_candidates):
            prioritized_prefix.append(other_candidates[other_index])
            other_index += 1
        elif explicit_index < len(explicit_candidates):
            prioritized_prefix.append(explicit_candidates[explicit_index])
            explicit_index += 1
        else:
            break

    selected_ids = {id(item) for item in prioritized_prefix}
    return prioritized_prefix + [
        item for item in scored_products if id(item) not in selected_ids
    ]


def normalize_chala_preference_payload(data: Any, user_id: int) -> dict:
    """Normalize new and legacy Chala responses without changing list fields."""

    data = data if isinstance(data, dict) else {}

    dimensions = {
        "categories": "category", "colors": "color", "styles": "style",
        "occasions": "occasion", "preferred_brands": "brand",
    }

    def list_value(field: str) -> list:
        value = data.get(field, [])
        return canonicalize_values(value if isinstance(value, list) else [], dimensions[field])

    def dict_value(field: str) -> dict:
        value = data.get(field, {})
        return value if isinstance(value, dict) else {}

    def weight_value(field: str, dimension: str) -> dict:
        return canonicalize_weight_map(dict_value(field), dimension)

    normalized_sources = {}
    for dimension, source_map in dict_value("preference_sources").items():
        if not isinstance(source_map, dict):
            continue
        singular_dimension = {
            "categories": "category", "colors": "color", "styles": "style",
            "occasions": "occasion", "preferred_brands": "brand",
        }.get(dimension, dimension)
        normalized_sources[dimension] = {}
        for value, sources in source_map.items():
            key = canonicalize_attribute(value, singular_dimension)
            if not key:
                continue
            target = normalized_sources[dimension].setdefault(key, [])
            for source in normalize_text_list(sources):
                if source not in target:
                    target.append(source)

    return {
        "user_id": data.get("user_id", user_id),
        "categories": list_value("categories"),
        "colors": list_value("colors"),
        "styles": list_value("styles"),
        "occasions": list_value("occasions"),
        "preferred_brands": list_value("preferred_brands"),
        "category_weights": weight_value("category_weights", "category"),
        "color_weights": weight_value("color_weights", "color"),
        "style_weights": weight_value("style_weights", "style"),
        "brand_weights": weight_value("brand_weights", "brand"),
        "occasion_weights": weight_value("occasion_weights", "occasion"),
        "preference_sources": normalized_sources,
    }

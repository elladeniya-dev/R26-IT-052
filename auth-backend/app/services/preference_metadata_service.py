"""Build backward-compatible weight and source metadata for preferences."""

from typing import Any

from app.services.fashion_attribute_normalizer import canonicalize_attribute


ML_ONLY_WEIGHT_CAP = 0.60


DIMENSIONS = {
    "categories": "category_weights",
    "colors": "color_weights",
    "styles": "style_weights",
    "preferred_brands": "brand_weights",
    "occasions": "occasion_weights",
}


def _clamp_weight(value: Any, maximum: float = 1.0) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 0.0

    return round(max(0.0, min(maximum, numeric_value)), 4)


def _ml_expansion_weight(expansion: dict) -> float:
    """Use the model's normalized probability, with uplift as a fallback."""

    confidence = expansion.get("probability")
    if confidence is None:
        confidence = expansion.get("uplift")

    return _clamp_weight(confidence, maximum=ML_ONLY_WEIGHT_CAP)


def build_weighted_preference_metadata(
    flat_preferences: dict | None,
    explicit_preferences: dict | None,
    learned_weights: dict | None,
    ml_expansions: dict | None,
) -> dict:
    """
    Merge explicit, learned, and ML evidence case-insensitively.

    The effective confidence is the strongest confidence from any source. Flat
    preference values keep their existing spelling and order; metadata may also
    describe source values that are temporarily absent from a truncated current
    profile.
    """

    flat_preferences = flat_preferences or {}
    explicit_preferences = explicit_preferences or {}
    learned_weights = learned_weights or {}
    ml_expansions = ml_expansions or {}

    result = {weight_field: {} for weight_field in DIMENSIONS.values()}
    preference_sources = {dimension: {} for dimension in DIMENSIONS}

    for dimension, weight_field in DIMENSIONS.items():
        effective_weights = {}
        sources_by_key = {}

        def register(value: Any) -> str | None:
            if value is None or not str(value).strip():
                return None

            key = canonicalize_attribute(value, dimension)
            if not key:
                return None
            sources_by_key.setdefault(key, [])
            return key

        def add_evidence(value: Any, source: str, weight: Any) -> None:
            key = register(value)
            if key is None:
                return

            if source not in sources_by_key[key]:
                sources_by_key[key].append(source)

            effective_weights[key] = max(
                effective_weights.get(key, 0.0),
                _clamp_weight(weight),
            )

        for value in flat_preferences.get(dimension, []) or []:
            register(value)

        for value in explicit_preferences.get(dimension, []) or []:
            add_evidence(value, "explicit", 1.0)

        dimension_learned_weights = learned_weights.get(weight_field, {}) or {}
        if isinstance(dimension_learned_weights, dict):
            for value, weight in dimension_learned_weights.items():
                add_evidence(value, "learned", weight)

        dimension_expansions = ml_expansions.get(dimension, []) or []
        if isinstance(dimension_expansions, list):
            for expansion in dimension_expansions:
                if not isinstance(expansion, dict):
                    continue
                value = expansion.get("preference")
                add_evidence(
                    value,
                    "ml_expansion",
                    _ml_expansion_weight(expansion),
                )

        for key in sources_by_key:
            # A defensive fallback preserves today's flat-list behavior if an
            # older/internal source produced a value without source metadata.
            result[weight_field][key] = round(
                effective_weights.get(key, 1.0),
                4,
            )
            preference_sources[dimension][key] = sources_by_key[key]

    result["preference_sources"] = preference_sources
    return result

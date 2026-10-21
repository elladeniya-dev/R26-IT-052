"""Canonical normalization for Koji product and preference attributes."""

import re
from collections.abc import Iterable, Mapping
from typing import Any


_SEPARATOR_RE = re.compile(r"[\s_\-/]+")
_CATEGORY_ALIASES = {
    "top": "top", "tops": "top",
    "tshirt": "tshirt", "tshirts": "tshirt", "tee": "tshirt", "tees": "tshirt",
    "shirt": "shirt", "shirts": "shirt",
    "dress": "dress", "dresses": "dress",
    "jean": "jeans", "jeans": "jeans",
    "trouser": "pants", "trousers": "pants", "pant": "pants", "pants": "pants",
    "skirt": "skirt", "skirts": "skirt",
    "short": "shorts", "shorts": "shorts",
    "jacket": "jacket", "jackets": "jacket",
    "blazer": "blazer", "blazers": "blazer",
    "sweater": "sweater", "sweaters": "sweater",
    "hoodie": "hoodie", "hoodies": "hoodie",
    "legging": "leggings", "leggings": "leggings",
}
_STYLE_ALIASES = {
    "smartcasual": "smart_casual",
    "partywear": "party", "party": "party",
    "comfortwear": "comfort", "comfort": "comfort",
    "workwear": "workwear",
}


def _base_key(value: Any) -> str:
    text = str(value or "").strip().casefold()
    return _SEPARATOR_RE.sub("_", text).strip("_")


def canonicalize_attribute(value: Any, dimension: str | None = None) -> str:
    key = _base_key(value)
    if not key:
        return ""
    collapsed = key.replace("_", "")
    if dimension in {"category", "categories"}:
        return _CATEGORY_ALIASES.get(collapsed, key)
    if dimension in {"style", "styles"}:
        return _STYLE_ALIASES.get(collapsed, key)
    return key


def canonicalize_values(values: Any, dimension: str | None = None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    elif not isinstance(values, Iterable):
        values = [values]

    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = canonicalize_attribute(value, dimension)
        if key and key not in seen:
            seen.add(key)
            result.append(key)
    return result


def canonicalize_weight_map(
    weights: Mapping[str, Any] | None,
    dimension: str | None = None,
) -> dict[str, float]:
    result: dict[str, float] = {}
    for value, raw_weight in (weights or {}).items():
        key = canonicalize_attribute(value, dimension)
        if not key:
            continue
        try:
            weight = max(0.0, min(1.0, float(raw_weight)))
        except (TypeError, ValueError):
            continue
        result[key] = max(result.get(key, 0.0), weight)
    return result


def tokenize_attribute_values(values: Any, dimension: str) -> list[str]:
    if values is None:
        return []
    raw_values = values if isinstance(values, (list, tuple, set)) else [values]
    tokens: list[Any] = []
    for value in raw_values:
        if isinstance(value, str):
            tokens.extend(re.split(r"[,;|]+", value))
        else:
            tokens.append(value)
    return canonicalize_values(tokens, dimension)

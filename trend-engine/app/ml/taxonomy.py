"""Canonical garment vocabulary shared with partner catalogues, with a family hierarchy.

A product from any catalogue is reduced to canonical attributes (the same words the trend engine
scores). Matching is exact on the leaf value, or on its family at reduced weight, so "blazer" can
meet a rising "jacket" trend and "off white" a rising "white" one without any fuzzy string logic.
Bump TAXONOMY_VERSION whenever a mapping changes; consumers can pin to it.
"""
from __future__ import annotations

import re
from collections import defaultdict

from app.ml.attr_clean import normalize_color
from app.ml.category_map import map_category
from app.ml.extractors import extract_material, extract_style_attrs

TAXONOMY_VERSION = "2026.10.3"

# Partner labels are sometimes wrong in ways the title gives away: a "Flared Leg Formal Pant" filed
# under blazer, or a "Basic Blazer" filed as a generic top. A title that names only a bottom garment
# (or only outerwear while the label is a generic top) is trusted over the label.
_BOTTOM_WORD = re.compile(
    r"\b(pants?|trousers?|jeans?|joggers?|skirts?|skorts?|shorts?(?!\s+sleeve)|leggings?)\b", re.IGNORECASE
)
_OUTER_WORD = re.compile(r"\b(blazers?|jackets?|coats?)\b", re.IGNORECASE)
_OTHER_GARMENT_WORD = re.compile(
    r"\b(tops?|tees?|t-?shirts?|shirts?|blouses?|tanks?|bodysuits?|sweaters?|cardigans?|hoodies?"
    r"|dress(?:es)?|jumpsuits?|rompers?|sets?|suits?)\b",
    re.IGNORECASE,
)


def _title_category_override(title: str, label_categories: set[str]) -> str | None:
    """Category implied by the title when it contradicts the partner label, else None."""
    bottom = _BOTTOM_WORD.search(title)
    outer = _OUTER_WORD.search(title)
    other = _OTHER_GARMENT_WORD.search(title)
    if bottom and not outer and not other:
        mapped = map_category(bottom.group(0)).lower()
        return mapped if mapped != "unknown" else None
    if outer and not bottom and not other and label_categories <= {"top", "unknown"}:
        mapped = map_category(outer.group(0)).lower()
        return mapped if mapped != "unknown" else None
    return None

# A family means "close substitutes", not a loose bucket: a rising "jacket" can meet a blazer,
# but a rising "blouse" must not boost every top, and "burgundy" must not boost every red item.
# A family means "close substitutes", not a loose bucket: a rising "jacket" can meet a blazer,
# but a rising "blouse" must not boost every top, and "burgundy" must not boost every red item.
CATEGORY_FAMILIES = {
    "outerwear": ["jacket", "blazer", "coat"],
    "knitwear": ["sweater", "cardigan", "hoodie"],
    "shirting": ["shirt", "blouse"],
    "legwear": ["trousers", "leggings/tights"],
    "one-piece": ["jumpsuit/playsuit", "dungarees"],
}

COLOR_FAMILIES = {
    "white": ["white", "off white", "cream"],
    "blue": ["blue", "navy"],
}

# Lengths such as midi/maxi only describe these garments ("Midi 6 Short" is a product-line name).
LENGTH_CATEGORIES = {"dress", "skirt", "jumpsuit/playsuit", "coat", "garment set"}
ANY_CATEGORY_LENGTHS = {"cropped"}

_FAMILY_INDEX: dict[str, dict[str, str]] = {"category": {}, "color": {}}
for _family, _leaves in CATEGORY_FAMILIES.items():
    for _leaf in _leaves:
        _FAMILY_INDEX["category"][_leaf] = _family
for _family, _leaves in COLOR_FAMILIES.items():
    for _leaf in _leaves:
        _FAMILY_INDEX["color"][_leaf] = _family

ATTR_TYPES = (
    "category", "color", "fabric", "pattern", "garment_length", "sleeve_length", "neckline", "style_detail",
)


def family_of(attr_type: str, value: str) -> str | None:
    """Family a leaf value belongs to, or None for types without a hierarchy (fabric, pattern, ...)."""
    return _FAMILY_INDEX.get(attr_type, {}).get(value)


def canonical_attributes(product: dict) -> dict[str, set[str]]:
    """Reduce a partner product descriptor to canonical attribute values.

    Expected keys (all optional): title, description, category, subcategory, colors, tags.
    """
    title = str(product.get("title") or "")
    description = str(product.get("description") or "")
    tags = [str(t) for t in (product.get("tags") or [])]
    attrs: dict[str, set[str]] = defaultdict(set)

    for raw in (product.get("subcategory"), product.get("category")):
        mapped = map_category(str(raw or "")).lower()
        if mapped != "unknown":
            attrs["category"].add(mapped)
            break
    if not attrs["category"]:
        mapped = map_category(title).lower()
        if mapped != "unknown":
            attrs["category"].add(mapped)

    override = _title_category_override(title, attrs["category"])
    if override:
        attrs["category"] = {override}

    for raw in product.get("colors") or []:
        color = normalize_color(str(raw))
        if color:
            attrs["color"].add(color)

    fabric = extract_material(f"{description} {title}") or next(
        (m for m in (extract_material(t) for t in tags) if m), None
    )
    if fabric:
        attrs["fabric"].add(fabric)

    for attr_type, value in extract_style_attrs(f"{title} {' '.join(tags)}"):
        if attr_type == "garment_length" and value not in ANY_CATEGORY_LENGTHS                 and not (attrs["category"] & LENGTH_CATEGORIES):
            continue
        attrs[attr_type].add(value)

    return attrs

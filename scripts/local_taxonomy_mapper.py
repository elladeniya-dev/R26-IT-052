"""
Free, local, deterministic replacement for the Gemini taxonomy-mapping step.
Maps messy raw extracted strings (e.g. "Acid Blue", "Tops", "Striped") onto
the strict, closed H&M taxonomy lists using hand-written synonym rules first,
then fuzzy string matching (stdlib difflib, no external dependency/cost) as
a fallback. Only returns "Unknown"/"Solid" if nothing reasonably matches.
"""
import difflib
import re

from scripts.ml_taxonomy import HM_CATEGORIES, HM_COLORS, HM_PATTERNS

CATEGORY_SYNONYMS = {
    "top": "Top", "tops": "Top", "tank": "Vest top", "tank top": "Vest top",
    "camisole": "Vest top", "cami": "Vest top",
    "tshirt": "T-shirt", "t-shirt": "T-shirt", "tee": "T-shirt",
    "sweater": "Sweater", "jumper": "Sweater", "pullover": "Sweater",
    "leggings": "Leggings/Tights", "tights": "Leggings/Tights",
    "bodysuit": "Bodysuit",
    "trouser": "Trousers", "trousers": "Trousers", "pant": "Trousers",
    "pants": "Trousers", "jeans": "Trousers", "denim pants": "Trousers",
    "skirt": "Skirt", "skirts": "Skirt", "midi skirt": "Skirt",
    "dress": "Dress", "dresses": "Dress", "midi dress": "Dress",
    "maxi dress": "Dress", "mini dress": "Dress", "gown": "Dress",
    "dresses & jumpsuits": "Dress",
    "short": "Shorts", "shorts": "Shorts",
    "cardigan": "Cardigan",
    "hoodie": "Hoodie", "hoody": "Hoodie", "sweatshirt": "Hoodie",
    "jumpsuit": "Jumpsuit/Playsuit", "playsuit": "Jumpsuit/Playsuit",
    "romper": "Jumpsuit/Playsuit",
    "jacket": "Jacket",
    "coat": "Coat",
    "polo": "Polo shirt", "polo shirt": "Polo shirt",
    "shirt": "Shirt",
    "blazer": "Blazer",
    "blouse": "Blouse",
    "dungaree": "Dungarees", "dungarees": "Dungarees", "overall": "Dungarees",
    "waistcoat": "Tailored Waistcoat", "vest": "Tailored Waistcoat",
    "set": "Garment Set", "co-ord": "Garment Set", "coord": "Garment Set",
}

# Base colors that already exist verbatim in HM_COLORS, keyed lowercase.
_HM_COLOR_LOOKUP = {c.lower(): c for c in HM_COLORS}

COLOR_SYNONYMS = {
    "navy": "Dark Blue", "maroon": "Dark Red", "burgundy": "Dark Red",
    "wine": "Dark Red", "mustard": "Dark Yellow", "olive": "Greenish Khaki",
    "khaki": "Greenish Khaki", "teal": "Dark Turquoise", "cream": "Off White",
    "ivory": "Off White", "ecru": "Off White", "stone": "Beige",
    "sand": "Beige", "camel": "Light Beige", "tan": "Light Beige",
    "nude": "Light Beige", "blush": "Light Pink", "rose": "Pink",
    "fuchsia": "Dark Pink", "magenta": "Dark Pink", "coral": "Light Orange",
    "rust": "Dark Orange", "mint": "Light Green", "sage": "Green",
    "lime": "Light Yellow", "lemon": "Light Yellow", "charcoal": "Dark Grey",
    "cobalt": "Blue", "aqua": "Turquoise", "denim": "Blue",
    "lavender": "Light Purple", "lilac": "Light Purple", "indigo": "Dark Purple",
    "gold": "Gold", "silver": "Silver", "bronze": "Bronze/Copper",
    "copper": "Bronze/Copper", "peach": "Light Orange",
}

# Modifier words that shift a base color into a Light/Dark H&M variant.
LIGHT_MODIFIERS = {"light", "pastel", "pale", "soft", "baby"}
DARK_MODIFIERS = {"dark", "deep", "acid", "bright", "bold"}

PATTERN_SYNONYMS = {
    "solid": "Solid", "plain": "Solid",
    "stripe": "Stripe", "striped": "Stripe", "stripes": "Stripe",
    "check": "Check", "checked": "Check", "checkered": "Check", "plaid": "Check",
    "dot": "Dot", "dots": "Dot", "polka dot": "Dot", "polka": "Dot",
    "floral": "Placement print", "flower": "Placement print",
    "print": "Front print", "printed": "Front print", "graphic": "Front print",
    "lace": "Lace", "sequin": "Sequin", "sequins": "Sequin", "sequinned": "Sequin",
    "embroidered": "Embroidery", "embroidery": "Embroidery",
    "mesh": "Mesh", "sheer": "Transparent", "transparent": "Transparent",
    "metallic": "Metallic", "glitter": "Glittering/Metallic",
    "colour block": "Colour blocking", "color block": "Colour blocking",
    "colorblock": "Colour blocking", "argyle": "Argyle", "jacquard": "Jacquard",
    "chambray": "Chambray", "melange": "Melange", "denim": "Denim",
}


def _fuzzy_match(value: str, candidates: list, cutoff: float = 0.75):
    matches = difflib.get_close_matches(value.lower(), [c.lower() for c in candidates], n=1, cutoff=cutoff)
    if not matches:
        return None
    for c in candidates:
        if c.lower() == matches[0]:
            return c
    return None


def map_category(raw_category: str) -> str:
    if not raw_category:
        return "Unknown"
    value = raw_category.strip().lower()
    value = re.sub(r"[^a-z0-9 &/-]", "", value)

    if raw_category in HM_CATEGORIES:
        return raw_category
    if value in CATEGORY_SYNONYMS:
        return CATEGORY_SYNONYMS[value]

    # Substring match against synonym keys (handles "Women's Midi Dress" etc.)
    for key, mapped in CATEGORY_SYNONYMS.items():
        if key in value:
            return mapped

    fuzzy = _fuzzy_match(value, HM_CATEGORIES, cutoff=0.7)
    return fuzzy or "Unknown"


def map_color(raw_color: str) -> str:
    if not raw_color:
        return "Unknown"
    value = raw_color.strip().lower()
    words = value.split()

    if raw_color in HM_COLORS:
        return raw_color
    if value in _HM_COLOR_LOOKUP:
        return _HM_COLOR_LOOKUP[value]

    modifier = None
    base_words = []
    for w in words:
        if w in LIGHT_MODIFIERS:
            modifier = "Light"
        elif w in DARK_MODIFIERS:
            modifier = "Dark"
        else:
            base_words.append(w)
    base = " ".join(base_words).strip()

    base_hm = _HM_COLOR_LOOKUP.get(base) or COLOR_SYNONYMS.get(base)
    if base_hm:
        if modifier and not base_hm.startswith(("Light", "Dark")):
            candidate = f"{modifier} {base_hm}"
            if candidate in HM_COLORS:
                return candidate
        return base_hm

    if value in COLOR_SYNONYMS:
        return COLOR_SYNONYMS[value]

    # RGB color-space distance — more principled than string-edit-distance
    # fuzzy matching for genuine color synonyms (e.g. "crimson" -> "Red" isn't
    # a spelling variant, it's a color relationship difflib can't see).
    from scripts.color_matcher import match_color_by_distance
    rgb_match = match_color_by_distance(value)
    if rgb_match:
        return rgb_match

    fuzzy = _fuzzy_match(value, HM_COLORS, cutoff=0.7)
    return fuzzy or "Unknown"


def map_pattern(raw_pattern: str) -> str:
    if not raw_pattern:
        return "Solid"
    value = raw_pattern.strip().lower()

    if raw_pattern in HM_PATTERNS:
        return raw_pattern
    if value in PATTERN_SYNONYMS:
        return PATTERN_SYNONYMS[value]

    for key, mapped in PATTERN_SYNONYMS.items():
        if key in value:
            return mapped

    fuzzy = _fuzzy_match(value, HM_PATTERNS, cutoff=0.7)
    return fuzzy or "Solid"


def map_attributes_locally(raw_category: str, raw_color: str, raw_pattern: str) -> dict:
    return {
        "mapped_category": map_category(raw_category),
        "mapped_color": map_color(raw_color),
        "mapped_pattern": map_pattern(raw_pattern),
    }

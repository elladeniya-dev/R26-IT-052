"""Cleans raw attribute labels before they reach the panel builder.

Fixed domain rules only (no fitting to outcomes): collapse colour shades onto
base colours, drop labels that are not really colours, drop the 'unknown' category.
"""
import re

import pandas as pd

COLOR_MODIFIERS = {
    "light", "dark", "mid", "deep", "bright", "pastel", "jet", "soft", "pale",
    "dusty", "hot", "baby", "electric", "neon", "medium", "royal", "sky",
}

COLOR_SYNONYMS = {
    "gray": "grey", "charcoal": "grey",
    "navy blue": "navy",
    "off-white": "off white", "offwhite": "off white", "ivory": "off white",
    "ecru": "off white", "cream": "off white",
    "wine": "burgundy", "maroon": "burgundy",
    "sand": "beige", "stone": "beige",
    "olive green": "olive", "cobalt": "blue", "indigo": "blue",
}

BASE_COLORS = {
    "black", "white", "off white", "grey", "red", "blue", "navy", "green",
    "yellow", "orange", "pink", "purple", "brown", "beige", "burgundy", "teal",
    "mustard", "olive", "khaki", "coral", "lavender", "lilac", "turquoise",
    "gold", "silver", "nude", "blush", "rust", "camel", "mint", "sage", "peach",
    "fuchsia", "rose", "tan", "magenta",
}


def normalize_color(raw: str) -> str | None:
    value = re.sub(r"\s+", " ", str(raw).lower().replace("-", " ").strip())
    if value in COLOR_SYNONYMS:
        value = COLOR_SYNONYMS[value]
    tokens = [t for t in value.split() if t not in COLOR_MODIFIERS]
    value = " ".join(tokens)
    value = COLOR_SYNONYMS.get(value, value)
    return value if value in BASE_COLORS else None


def clean_attributes(attrs_long: pd.DataFrame) -> pd.DataFrame:
    if attrs_long.empty:
        return attrs_long
    out = attrs_long.copy()
    attr_type = out["attr_type"].astype(str).str.replace("AttrType.", "", regex=False)
    is_color = attr_type == "color"
    out.loc[is_color, "attr"] = out.loc[is_color, "attr"].map(normalize_color)
    out = out[out["attr"].notna()]
    attr_type = out["attr_type"].astype(str).str.replace("AttrType.", "", regex=False)
    out = out[~((attr_type == "category") & (out["attr"] == "unknown"))]
    return out.drop_duplicates(["date", "product_id", "attr_type", "attr"])

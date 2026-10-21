"""Segment trends: attribute COMBINATIONS such as "white + dress" or "satin + top".

A single rising attribute does not make a particular garment trending: white can be rising while a given
white garment is not. A segment is two attributes carried by the same product, tracked and forecast with the
same pipeline and the same truth measure (change in share of listings) as single attributes. The engine scores
a segment from the series of products that carry both parts.
"""
from __future__ import annotations

import pandas as pd

# (part 1, part 2). Pairs are chosen so both parts describe the garment itself.
SEGMENT_PAIRS: tuple[tuple[str, str], ...] = (
    ("color", "category"),
    ("fabric", "category"),
    ("color", "fabric"),
    ("category", "neckline"),
    ("category", "sleeve_length"),
    ("category", "pattern"),
)
SEGMENT_TYPES: tuple[str, ...] = tuple(f"{a}_x_{b}" for a, b in SEGMENT_PAIRS)
SEPARATOR = " + "


def segment_type(part1_type: str, part2_type: str) -> str:
    return f"{part1_type}_x_{part2_type}"


def is_segment_type(attr_type: str) -> bool:
    return attr_type in SEGMENT_TYPES


def parse_segment(seg_type: str, value: str) -> tuple[tuple[str, str], tuple[str, str]]:
    """('color_x_category', 'white + dress') -> (('color', 'white'), ('category', 'dress'))."""
    type1, type2 = seg_type.split("_x_", 1)
    value1, value2 = value.split(SEPARATOR, 1)
    return (type1, value1), (type2, value2)


def segment_rows(attrs_long: pd.DataFrame) -> pd.DataFrame:
    """Turn the long attribute table (date, product_id, brand, attr_type, attr) into segment rows in the same
    shape, so they can go through the same panel builder and engine as single attributes."""
    attrs = attrs_long.copy()
    attrs["attr_type"] = attrs["attr_type"].astype(str).str.replace("AttrType.", "", regex=False)
    attrs = attrs[attrs["attr"].notna() & (attrs["attr"] != "")]

    parts = []
    for type1, type2 in SEGMENT_PAIRS:
        left = attrs[attrs.attr_type == type1][["date", "product_id", "brand", "attr"]].rename(columns={"attr": "v1"})
        right = attrs[attrs.attr_type == type2][["date", "product_id", "brand", "attr"]].rename(columns={"attr": "v2"})
        merged = left.merge(right, on=["date", "product_id", "brand"])
        if merged.empty:
            continue
        merged["attr_type"] = segment_type(type1, type2)
        merged["attr"] = merged.v1.astype(str) + SEPARATOR + merged.v2.astype(str)
        parts.append(merged[["date", "product_id", "brand", "attr_type", "attr"]])

    if not parts:
        return pd.DataFrame(columns=["date", "product_id", "brand", "attr_type", "attr"])
    return pd.concat(parts, ignore_index=True)

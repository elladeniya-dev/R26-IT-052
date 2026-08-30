"""Category-only normalization onto a closed taxonomy. Used by jobs/ingest.py. See docs/trend-engine-guide.html."""
import difflib
import re

HM_CATEGORIES = [
    "Vest top", "Sweater", "Top", "Leggings/Tights", "Bodysuit", "Trousers",
    "Skirt", "T-shirt", "Dress", "Shorts", "Cardigan", "Hoodie",
    "Jumpsuit/Playsuit", "Jacket", "Coat", "Polo shirt", "Shirt", "Blazer",
    "Blouse", "Outdoor overall", "Dungarees", "Tailored Waistcoat", "Garment Set",
    "Outdoor Waistcoat", "Outdoor trousers",
]

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


def map_category(raw_category: str) -> str:
    if not raw_category:
        return "Unknown"
    value = raw_category.strip().lower()
    value = re.sub(r"[^a-z0-9 &/-]", "", value)

    if raw_category in HM_CATEGORIES:
        return raw_category
    if value in CATEGORY_SYNONYMS:
        return CATEGORY_SYNONYMS[value]

    for key, mapped in CATEGORY_SYNONYMS.items():
        if key in value:
            return mapped

    matches = difflib.get_close_matches(value, [c.lower() for c in HM_CATEGORIES], n=1, cutoff=0.7)
    if matches:
        for c in HM_CATEGORIES:
            if c.lower() == matches[0]:
                return c
    return "Unknown"

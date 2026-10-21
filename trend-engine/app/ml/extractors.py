"""Shared attribute vocabularies and text extractors.
Used by jobs/ingest.py (scraped catalogue) and by the product-scoring service (partner catalogues),
so both sides describe a garment with the same words. See app/ml/taxonomy.py for the hierarchy."""
from __future__ import annotations

import re

KNOWN_MATERIALS = {
    "cotton", "linen", "denim", "silk", "satin", "chiffon", "velvet", "leather",
    "lace", "knit", "jersey", "viscose", "rayon", "nylon", "spandex", "crepe",
    "polyester", "wool", "cashmere", "corduroy", "suede", "organza", "tulle",
    "georgette", "modal", "fleece", "twill", "canvas", "chambray", "lycra",
    "cotton blend", "faux leather", "vegan leather", "tencel", "rib fabric",
    "ribbed", "ponte", "scuba", "neoprene", "elastane",
}


KNOWN_SLEEVE_TYPES = sorted([
    "sleeveless", "cap sleeve", "short sleeve", "3/4 sleeve", "elbow sleeve",
    "long sleeve", "puff sleeve", "bell sleeve", "bishop sleeve",
], key=len, reverse=True)

KNOWN_NECKLINES = sorted([
    "crew neck", "round neck", "v neck", "v-neck", "square neck",
    "off shoulder", "off-shoulder", "halter neck", "halter", "sweetheart neckline",
    "boat neck", "collar", "turtleneck", "cowl neck",
], key=len, reverse=True)

KNOWN_SILHOUETTES = sorted([
    "a-line", "a line", "bodycon", "wrap", "shift dress", "empire waist",
    "fit and flare", "asymmetric",
], key=len, reverse=True)

PATTERN_VOCAB = [
    ("floral", r"floral|flower|botanical|blossom"),
    ("striped", r"stripe|striped|pinstripe"),
    ("check", r"check|checked|plaid|gingham|tartan"),
    ("polka dot", r"polka|dots?|spotted"),
    ("animal print", r"leopard|zebra|animal|snake|cheetah"),
    ("tie dye", r"tie[\s-]?dye"),
    ("geometric", r"geometric"),
    ("paisley", r"paisley"),
    ("printed", r"printed|print"),
]

GARMENT_LENGTH_VOCAB = [
    ("mini", r"mini"),
    ("midi", r"midi"),
    ("maxi", r"maxi"),
    ("cropped", r"cropped|crop"),
    ("knee length", r"knee[\s-]?length"),
    ("ankle length", r"ankle[\s-]?length|ankle"),
]


def extract_material(text: str) -> str | None:
    if not text:
        return None
    value = text.lower()
    pct_matches = re.findall(r"(\d{1,3})\s*%\s*([A-Za-z][A-Za-z\s]{2,20})", value)
    if pct_matches:
        pct_matches.sort(key=lambda m: int(m[0]), reverse=True)
        for _, candidate_text in pct_matches:
            for material in sorted(KNOWN_MATERIALS, key=len, reverse=True):
                if material in candidate_text:
                    return material
    best_pos, best_material = None, None
    for material in KNOWN_MATERIALS:
        pos = value.find(material)
        if pos != -1 and (best_pos is None or pos < best_pos):
            best_pos, best_material = pos, material
    return best_material


def _first_match(text: str, vocab: list[tuple[str, str]]) -> str | None:
    for label, pattern in vocab:
        if re.search(rf"\b(?:{pattern})\b", text):
            return label
    return None


def extract_style_attrs(text: str) -> list[tuple[str, str]]:
    """Returns [(attr_type, value), ...] across sleeve_length/neckline/style_detail/pattern/garment_length."""
    if not text:
        return []
    value = text.lower()
    found = []
    for attr_type, vocab in (
        ("sleeve_length", KNOWN_SLEEVE_TYPES),
        ("neckline", KNOWN_NECKLINES),
        ("style_detail", KNOWN_SILHOUETTES),
    ):
        for term in vocab:
            if re.search(rf"\b{re.escape(term)}\b", value):
                found.append((attr_type, term))
                break  # only the first/longest match per vocabulary
    for attr_type, vocab in (("pattern", PATTERN_VOCAB), ("garment_length", GARMENT_LENGTH_VOCAB)):
        label = _first_match(value, vocab)
        if label:
            found.append((attr_type, label))
    return found

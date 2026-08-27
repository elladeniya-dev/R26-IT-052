"""
Parses store-authored "spec sheet" lines out of product body_html
(e.g. "Material: Rib Fabric", "Fit Type: Regular Fit", "Style: Long sleeve,
Square neck crop top"). Many Sri Lankan boutique Shopify stores write this
as an HTML table, one label:value pair per row — this is the store telling
us the answer directly, which is higher-confidence than guessing from a
title or filename. Falls back to nothing if the store doesn't write specs
this way; never invents a value.
"""
import re

# Maps the many label spellings stores actually use to our schema fields.
LABEL_MAP = {
    "material": "material",
    "fabric": "material",
    "composition": "material",
    "composition - fabric": "material",
    "fabric composition": "material",
    "color": "color",
    "colour": "color",
    "fit type": "fit_type",
    "fit": "fit_type",
    "style": "style",
    "sleeve": "style",
    "neckline": "style",
}

_LINE_BREAK_TAGS = re.compile(r"</(tr|p|li|div)\s*>|<br\s*/?>", re.IGNORECASE)
_TAG_STRIP = re.compile(r"<[^>]+>")
_LABEL_LINE = re.compile(r"^\s*([A-Za-z][A-Za-z /\-]{1,25}?)\s*[:\-]\s*(.{1,150})\s*$")


def parse_spec_fields(html: str) -> dict:
    """Returns whatever of {material, color, fit_type, style} the description states explicitly."""
    if not html:
        return {}

    # Turn block-level boundaries into newlines before stripping tags,
    # otherwise every spec line collapses into one unparseable blob.
    text = _LINE_BREAK_TAGS.sub("\n", html)
    text = _TAG_STRIP.sub("", text)
    text = text.replace("&amp;", "&")

    found = {}
    for line in text.split("\n"):
        match = _LABEL_LINE.match(line.strip())
        if not match:
            continue
        label = match.group(1).strip().lower()
        value = match.group(2).strip()
        field = LABEL_MAP.get(label)
        if field and field not in found and value and value.lower() not in ("n/a", "na", "-"):
            found[field] = value

    return found

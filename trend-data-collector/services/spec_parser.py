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


_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def _denormalize(raw: str) -> str:
    """Some platforms embed the description as an escaped JSON string inside a
    <script> blob rather than literal HTML (e.g. \\u003cli\\u003eColor : Beige
    \\u003c/li\\u003e). Decode that back to real characters before parsing —
    without this, the spec lines are invisible even though the data is there."""
    text = _UNICODE_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), raw)
    text = text.replace("\\n", "\n").replace("\\t", " ")
    return text


def parse_spec_fields(html: str) -> dict:
    """Returns whatever of {material, color, fit_type, style} the description states explicitly."""
    if not html:
        return {}

    if "\\u003c" in html or "\\u0026" in html:
        html = _denormalize(html)

    # Turn block-level boundaries into newlines before stripping tags,
    # otherwise every spec line collapses into one unparseable blob.
    text = _LINE_BREAK_TAGS.sub("\n", html)
    text = _TAG_STRIP.sub("", text)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ")

    found = {}
    for line in text.split("\n"):
        match = _LABEL_LINE.match(line.strip())
        if not match:
            continue
        label = match.group(1).strip().lower()
        # Strip leading bullet/symbol characters (•, ●, emoji, etc.) that some
        # stores prefix values with — otherwise they leak into the stored value.
        value = re.sub(r"^[^\w\d]+", "", match.group(2).strip()).strip()
        field = LABEL_MAP.get(label)
        if field and field not in found and value and value.lower() not in ("n/a", "na", "-"):
            found[field] = value

    return found

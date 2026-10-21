"""Eligibility check used when mirroring Koji products into Chala."""

import re


_NON_FASHION_PATTERNS = (
    re.compile(r"\bgift[\s\-\u2010-\u2015]+cards?\b", re.IGNORECASE),
    re.compile(r"\be[\s\-\u2010-\u2015]*gift\s+cards?\b", re.IGNORECASE),
    re.compile(r"\bgift[\s\-\u2010-\u2015]+vouchers?\b", re.IGNORECASE),
    re.compile(r"\bvouchers?\b", re.IGNORECASE),
    re.compile(r"\bstore\s+credits?\b", re.IGNORECASE),
)


def is_non_fashion_product(product) -> bool:
    def value(field):
        return product.get(field) if isinstance(product, dict) else getattr(product, field, None)

    text = " | ".join(
        str(value(field))
        for field in ("title", "product_name", "category", "description")
        if value(field) is not None
    )
    return any(pattern.search(text) for pattern in _NON_FASHION_PATTERNS)

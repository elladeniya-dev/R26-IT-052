"""Catalog eligibility rules shared by ingestion and recommendation paths."""

import re
from typing import Any


_NON_FASHION_PATTERNS = (
    re.compile(r"\bgift[\s\-\u2010-\u2015]+cards?\b", re.IGNORECASE),
    re.compile(r"\be[\s\-\u2010-\u2015]*gift\s+cards?\b", re.IGNORECASE),
    re.compile(r"\bgift[\s\-\u2010-\u2015]+vouchers?\b", re.IGNORECASE),
    re.compile(r"\bvouchers?\b", re.IGNORECASE),
    re.compile(r"\bstore\s+credits?\b", re.IGNORECASE),
)

_INSPECTION_FIELDS = (
    "title", "product_name", "product_type", "type", "category", "subcategory",
    "tags", "description",
)


def _field_value(product: Any, field: str) -> Any:
    if isinstance(product, dict):
        return product.get(field)
    return getattr(product, field, None)


def is_non_fashion_product(product: Any) -> bool:
    """Reject vouchers/store credit without rejecting ordinary use of 'gift'."""

    values: list[str] = []
    for field in _INSPECTION_FIELDS:
        value = _field_value(product, field)
        if isinstance(value, (list, tuple, set)):
            values.extend(str(item) for item in value if item is not None)
        elif value is not None:
            values.append(str(value))

    searchable = " | ".join(values)
    return any(pattern.search(searchable) for pattern in _NON_FASHION_PATTERNS)

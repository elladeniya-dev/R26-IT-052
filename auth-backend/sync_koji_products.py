"""
Syncs Koji's product catalog into Chala's own `products` table.

Chala's Learning Engine and interaction-history endpoint both resolve
product attributes (category/color/style/brand) by looking up item_id
in Chala's local `products` table (see app/models.py:Product). That
table was already shaped to hold Koji's catalog but was never
populated with anything beyond 5 sample rows, so every interaction
against a real Koji product silently failed to resolve.

This script fetches Koji's live catalog and upserts it into that
table. Safe to re-run at any time (upsert by item_id).

Usage:
    python sync_koji_products.py
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

from app.database import SessionLocal  # noqa: E402
from app.models import Product  # noqa: E402
from app.services.fashion_attribute_normalizer import (  # noqa: E402
    canonicalize_attribute,
    tokenize_attribute_values,
)
from app.services.product_quality_service import is_non_fashion_product  # noqa: E402

KOJI_API_URL = os.getenv("KOJI_API_URL", "http://127.0.0.1:8002")


def fetch_koji_products() -> list[dict]:
    response = requests.get(f"{KOJI_API_URL.rstrip('/')}/products/", timeout=30)
    response.raise_for_status()
    return response.json()


def sync_products() -> None:
    products = fetch_koji_products()
    print(f"Fetched {len(products)} products from Koji ({KOJI_API_URL}).")

    db = SessionLocal()
    inserted = 0
    updated = 0
    skipped = 0
    removed = 0

    try:
        for existing_product in db.query(Product).all():
            if is_non_fashion_product(existing_product):
                db.delete(existing_product)
                removed += 1

        for item in products:
            item_id = item.get("item_id")
            if not item_id or is_non_fashion_product(item):
                skipped += 1
                continue

            existing = (
                db.query(Product).filter(Product.item_id == item_id).first()
            )

            if existing is None:
                existing = Product(item_id=item_id)
                db.add(existing)
                inserted += 1
            else:
                updated += 1

            existing.product_name = item.get("title")
            existing.category = canonicalize_attribute(
                item.get("category"), "category"
            ) or "unknown"
            existing.color = tokenize_attribute_values(item.get("color"), "color")
            existing.style = tokenize_attribute_values(item.get("style"), "style")
            existing.brand = canonicalize_attribute(item.get("brand"), "brand") or None
            existing.product_url = item.get("product_url")
            existing.image_url = item.get("image_url")

        db.commit()
        print(
            f"Done. Inserted {inserted}, updated {updated}, "
            f"skipped {skipped}, removed legacy {removed}."
        )
    finally:
        db.close()


if __name__ == "__main__":
    sync_products()

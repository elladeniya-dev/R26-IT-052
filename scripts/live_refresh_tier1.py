"""
Live-refreshes all TIER_1_SHOPIFY stores right now (not waiting for the next
daily run): updates price/original_price/in_stock/material/fit_type/style
for products already in the DB, and inserts genuinely new products (URLs
never seen before) as real new arrivals. Uses the same collector code the
daily harvester uses (services.tier1_shopify), just run on demand.
"""
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "trend-data-collector"))

from app.core.database import SessionLocal
from app.models import Product
from config.target_stores import SRI_LANKA_TARGET_STORES, TIER_1_SHOPIFY
from services.tier1_shopify import execute_tier1_shopify_json
from scripts.ingest_garments_etl import fast_raw_extraction, extract_material
from scripts.local_taxonomy_mapper import map_category, map_color, map_pattern


def refresh():
    db = SessionLocal()
    stores = [s for s in SRI_LANKA_TARGET_STORES if s["ingestion_tier"] == TIER_1_SHOPIFY]
    print(f"Refreshing {len(stores)} confirmed Shopify stores live...")

    updated = 0
    new_items = 0
    now_sale_items = []
    new_arrival_items = []

    for store in stores:
        print(f"  {store['brand_name']}...")
        try:
            garments = execute_tier1_shopify_json(store)
        except Exception as err:
            print(f"    ERROR: {err}")
            continue

        for g in garments:
            url = g.get("product_url")
            if not url:
                continue
            item_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
            existing = db.query(Product).filter(Product.item_id == item_id).first()

            original_price = g.get("original_price_lkr") or None
            in_stock = g.get("in_stock", True)

            if existing:
                existing.original_price = original_price
                existing.availability = in_stock
                if not existing.material and g.get("desc_material"):
                    existing.material = g["desc_material"]
                if not existing.fit_type and g.get("desc_fit_type"):
                    existing.fit_type = g["desc_fit_type"]
                if not existing.style and g.get("desc_style"):
                    existing.style = [g["desc_style"]]
                if not existing.description and g.get("description"):
                    existing.description = g["description"]
                updated += 1
                if original_price and original_price > (existing.price or 0):
                    now_sale_items.append((existing.title, existing.price, original_price, store["brand_name"]))
            else:
                raw_color, raw_pattern, raw_cat = fast_raw_extraction(g)
                material = g.get("desc_material") or extract_material(
                    " ".join([g.get("title", ""), g.get("description", "")])
                )
                product = Product(
                    item_id=item_id,
                    title=g.get("title", "Unknown"),
                    category=raw_cat or "Unknown",
                    color=[raw_color] if raw_color else [],
                    pattern=raw_pattern or "Solid",
                    material=material or None,
                    fit_type=g.get("desc_fit_type") or None,
                    style=[g["desc_style"]] if g.get("desc_style") else [],
                    price=g.get("price_lkr"),
                    original_price=original_price,
                    currency="LKR",
                    brand=g.get("source_name"),
                    source=g.get("source_type"),
                    product_url=url,
                    image_url=g.get("primary_image_url"),
                    description=g.get("description") or None,
                    availability=in_stock,
                    collected_at=datetime.now(timezone.utc),
                    ml_category=map_category(raw_cat),
                    ml_color=map_color(raw_color),
                    ml_pattern=map_pattern(raw_pattern),
                )
                db.add(product)
                new_items += 1
                new_arrival_items.append((product.title, store["brand_name"], product.price))

        db.commit()

    db.close()

    print(f"\n=== Live Refresh Complete ===")
    print(f"Existing products updated: {updated}")
    print(f"Genuinely new products discovered: {new_items}")
    print(f"Products currently discounted (original_price > price): {len(now_sale_items)}")

    if new_arrival_items:
        print("\nSample new arrivals:")
        for title, brand, price in new_arrival_items[:5]:
            print(f"  [{brand}] {title} — Rs.{price}")

    if now_sale_items:
        print("\nSample discounts:")
        for title, price, orig, brand in now_sale_items[:5]:
            pct = round(100 * (orig - price) / orig)
            print(f"  [{brand}] {title} — Rs.{price} (was Rs.{orig}, -{pct}%)")


if __name__ == "__main__":
    refresh()

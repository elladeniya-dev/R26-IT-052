"""
Syncs Koji's product catalog into this engine's own `products` table.

The outfit compatibility engine used to run its own crawlers against the
fashion sites, duplicating Koji's Data Collection component. Koji's
`products` table already holds the full catalog (same schema: item_id,
title, category, subcategory, color, style, brand, price, currency,
image_url, product_url, source, description, availability), so this
script reads it directly through the read-only KOJI_DATABASE_URL
credential and upserts it into the local table instead.

Safe to re-run at any time (upsert by item_id).

Usage:
    python scripts/s_sync_koji_products.py
"""

from pathlib import Path
import argparse
import os
import subprocess
import sys

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from dotenv import load_dotenv

load_dotenv(SERVER_ROOT / ".env")

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.s_database import SessionLocal, Base, engine as local_engine  # noqa: E402
from app.s_models import Product  # noqa: E402

KOJI_DATABASE_URL = os.getenv("KOJI_DATABASE_URL")
KOJI_PRODUCTS_TABLE = os.getenv("KOJI_PRODUCTS_TABLE", "products")

KOJI_COLUMNS = [
    "item_id",
    "title",
    "category",
    "subcategory",
    "color",
    "style",
    "brand",
    "price",
    "currency",
    "image_url",
    "product_url",
    "source",
    "description",
    "availability",
]


def fetch_koji_products() -> list[dict]:
    if not KOJI_DATABASE_URL:
        raise RuntimeError("KOJI_DATABASE_URL is missing in .env file")

    # Force the psycopg3 dialect (only driver installed in this venv) -
    # the bare "postgresql://" scheme defaults SQLAlchemy to psycopg2.
    koji_url = KOJI_DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )
    koji_engine = create_engine(koji_url)
    KojiSession = sessionmaker(bind=koji_engine)
    koji_db = KojiSession()

    try:
        columns_sql = ", ".join(KOJI_COLUMNS)
        rows = koji_db.execute(
            text(f"SELECT {columns_sql} FROM {KOJI_PRODUCTS_TABLE}")
        ).mappings().all()
        return [dict(row) for row in rows]
    finally:
        koji_db.close()


def sync_products() -> None:
    Base.metadata.create_all(bind=local_engine)

    products = fetch_koji_products()
    print(f"Fetched {len(products)} products from Koji's database.")

    db = SessionLocal()
    inserted = 0
    updated = 0
    skipped = 0

    try:
        for item in products:
            item_id = item.get("item_id")

            if not item_id:
                skipped += 1
                continue

            existing = db.query(Product).filter(Product.item_id == item_id).first()

            if existing is None:
                existing = Product(item_id=item_id)
                db.add(existing)
                inserted += 1
            else:
                updated += 1

            existing.title = item.get("title")
            existing.category = item.get("category")
            existing.subcategory = item.get("subcategory")
            existing.color = item.get("color") or []
            existing.style = item.get("style") or []
            existing.brand = item.get("brand")
            existing.price = item.get("price")
            existing.currency = item.get("currency")
            new_image_url = item.get("image_url")
            if existing.image_url != new_image_url:
                # The cached vector represents the old image; the backfill
                # script will regenerate it after this sync.
                existing.image_embedding = None
            existing.image_url = new_image_url
            existing.product_url = item.get("product_url")
            existing.source = item.get("source")
            existing.description = item.get("description")
            existing.availability = bool(item.get("availability", True))

        db.commit()
        print(f"Done. Inserted {inserted}, updated {updated}, skipped {skipped}.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-embeddings",
        action="store_true",
        help="Regenerate missing/stale image embeddings after syncing products.",
    )
    args = parser.parse_args()

    sync_products()
    if args.with_embeddings:
        subprocess.run(
            [
                sys.executable,
                str(SERVER_ROOT / "scripts" / "s_generate_embeddings.py"),
            ],
            cwd=SERVER_ROOT,
            check=True,
        )

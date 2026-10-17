"""Backfills sleeve/neckline/style/pattern/garment-length attributes from product titles.
Usage: python jobs/backfill_attributes.py. Safe to re-run (inserts are idempotent)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import Product  # noqa: E402
from jobs.ingest import clean_title, extract_style_attrs, upsert_attribute  # noqa: E402


def run() -> None:
    db = SessionLocal()
    try:
        added = 0
        for product_id, title in db.execute(select(Product.product_id, Product.title)).all():
            for attr_type, value in extract_style_attrs(clean_title(title or "")):
                upsert_attribute(db, product_id, attr_type, value)
                added += 1
        db.commit()
        print(f"processed titles, attempted {added} attribute inserts")
    finally:
        db.close()


if __name__ == "__main__":
    run()

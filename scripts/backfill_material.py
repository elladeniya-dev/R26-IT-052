"""
Populates Product.material for existing rows using the free keyword extractor,
against title + description already stored in Postgres. No re-scraping needed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models import Product
from app.pipeline.ingest_garments_etl import extract_material


def backfill():
    db = SessionLocal()

    candidates = db.query(Product).filter(Product.material.is_(None)).all()
    print(f"Found {len(candidates)} products with no material...")

    found = 0
    for p in candidates:
        text = " ".join(filter(None, [p.title, p.description]))
        material = extract_material(text)
        if material:
            p.material = material
            found += 1

    db.commit()
    db.close()
    print(f"Populated material for {found} / {len(candidates)} products.")


if __name__ == "__main__":
    backfill()

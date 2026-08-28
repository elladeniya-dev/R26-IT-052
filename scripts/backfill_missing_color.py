"""
Re-attempts color extraction for existing Products with no color, using the
new image-filename color scan (in addition to title) — no re-scraping needed
since title/image_url are already stored. Updates both the raw `color` and
the standardized `ml_color` for anything newly found. Products where truly
no color signal exists anywhere are left alone and stay excluded from
color-based trend analysis, as intended.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models import Product
from app.pipeline.ingest_garments_etl import _scan_text_for_color, clean_title, extract_image_name
from app.pipeline.local_taxonomy_mapper import map_color


def backfill():
    db = SessionLocal()

    candidates = db.query(Product).filter(
        (Product.color.is_(None)) | (__import__("sqlalchemy").func.cardinality(Product.color) == 0)
    ).all()

    print(f"Found {len(candidates)} products with no color to re-attempt...")

    found_from_title = 0
    found_from_image = 0
    still_nothing = 0

    for p in candidates:
        color = _scan_text_for_color(clean_title(p.title or ""))
        if color:
            found_from_title += 1
        else:
            img_name = extract_image_name(p.image_url or "")
            if img_name:
                color = _scan_text_for_color(img_name)
                if color:
                    found_from_image += 1

        if color:
            p.color = [color]
            p.ml_color = map_color(color)
        else:
            still_nothing += 1

    db.commit()
    db.close()

    print(f"Recovered from title: {found_from_title}")
    print(f"Recovered from image filename: {found_from_image}")
    print(f"Still no color found anywhere (left as-is, excluded from color trends): {still_nothing}")


if __name__ == "__main__":
    backfill()

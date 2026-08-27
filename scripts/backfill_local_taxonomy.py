"""
Re-maps ml_category/ml_color/ml_pattern for existing Product rows using the
free local taxonomy mapper (scripts/local_taxonomy_mapper.py), against the
raw category/color/pattern already stored in Postgres. No re-scraping, no
NLP re-run, no Gemini required — just fixes rows that were previously left
as "Unknown"/"Solid" (e.g. because Gemini quota was exhausted).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models import Product
from scripts.local_taxonomy_mapper import map_category, map_color, map_pattern


def backfill():
    db = SessionLocal()

    candidates = db.query(Product).filter(
        (Product.ml_category == "Unknown")
        | (Product.ml_color == "Unknown")
        | (Product.ml_pattern.is_(None))
    ).all()

    print(f"Found {len(candidates)} products to re-map...")

    updated = 0
    still_unknown_cat = 0
    still_unknown_col = 0

    for p in candidates:
        raw_color = p.color[0] if p.color else None
        new_cat = map_category(p.category)
        new_col = map_color(raw_color)
        new_pat = map_pattern(p.pattern)

        changed = (new_cat != p.ml_category) or (new_col != p.ml_color) or (new_pat != p.ml_pattern)
        if changed:
            p.ml_category = new_cat
            p.ml_color = new_col
            p.ml_pattern = new_pat
            updated += 1

        if new_cat == "Unknown":
            still_unknown_cat += 1
        if new_col == "Unknown":
            still_unknown_col += 1

        if updated % 200 == 0 and updated > 0:
            db.commit()

    db.commit()
    db.close()

    print(f"Updated {updated} rows.")
    print(f"Still Unknown after local mapping: category={still_unknown_cat}, color={still_unknown_col}")


if __name__ == "__main__":
    backfill()

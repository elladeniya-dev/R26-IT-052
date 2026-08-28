"""
Builds TrendObservation rows directly from the daily raw scrape snapshots
(trend-data-collector/output/run_*), instead of from the deduplicated
Products table. Each run folder is one real day of data with its own
rank_position per item, so this captures actual day-over-day movement
(growth, rank change, new arrivals) rather than a single flat snapshot.
"""
import glob
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.database import SessionLocal
from app.models import Product, TrendObservation

RUN_DIR_RE = re.compile(r"run_(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})(\d{2})$")


def parse_run_date(run_dir: str) -> datetime:
    name = os.path.basename(run_dir.rstrip("/\\"))
    m = RUN_DIR_RE.search(name)
    if not m:
        raise ValueError(f"Cannot parse date from run folder name: {name}")
    date_part, hh, mm, ss = m.groups()
    return datetime.strptime(f"{date_part} {hh}:{mm}:{ss}", "%Y-%m-%d %H:%M:%S")


def load_product_attributes(db) -> dict:
    """product_url -> (ml_category, ml_color, ml_pattern, material, style_tags)"""
    rows = db.query(
        Product.product_url, Product.ml_category, Product.ml_color, Product.ml_pattern,
        Product.material, Product.style,
    ).all()
    return {url: (cat, col, pat, mat, sty or []) for url, cat, col, pat, mat, sty in rows if url}


def generate_observations():
    db = SessionLocal()

    print("Wiping existing observations to prevent duplicates...")
    db.query(TrendObservation).delete()
    db.commit()

    print("Loading ML-standardized attributes for known products...")
    product_attrs = load_product_attributes(db)
    print(f"  {len(product_attrs)} products with known attributes.")

    root_dir = Path(__file__).resolve().parent.parent.parent
    run_folders = sorted(glob.glob(os.path.join(root_dir, "trend-data-collector", "output", "run_*")))
    if not run_folders:
        print("No run folders found.")
        db.close()
        return

    observations = []
    seen_items = set()  # url -> first-seen run date, used to flag new arrivals
    skipped_unknown_product = 0
    skipped_unmapped_attrs = 0

    for run_dir in run_folders:
        run_date = parse_run_date(run_dir)

        for file_path in glob.glob(os.path.join(run_dir, "*_garments.json")):
            if "combined" in file_path:
                continue
            try:
                garments = json.load(open(file_path, "r", encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            for garment in garments:
                url = garment.get("product_url")
                rank = garment.get("rank_position")
                if not url:
                    continue

                attrs = product_attrs.get(url)
                if attrs is None:
                    # Item was scraped but never made it into (or was filtered
                    # out of) the Products table — skip, nothing to attribute it to.
                    skipped_unknown_product += 1
                    continue

                ml_cat, ml_col, ml_pat, material, style_tags = attrs
                is_new_arrival = url not in seen_items
                if is_new_arrival:
                    seen_items.add(url)

                any_known_attr = False
                single_valued = (("category", ml_cat), ("color", ml_col), ("pattern", ml_pat), ("material", material))
                # style is an array (a product can have both a sleeve type and
                # a neckline) — one observation per tag, same as the others.
                multi_valued = [("style", tag) for tag in style_tags]

                for attr_type, attr_val in single_valued + tuple(multi_valued):
                    if not attr_val or attr_val == "Unknown":
                        continue
                    any_known_attr = True
                    observations.append(TrendObservation(
                        source_name="ecommerce_scraper",
                        source_type="ecommerce",
                        attribute_type=attr_type,
                        attribute_value=attr_val,
                        rank_position=rank,
                        collected_at=run_date,
                    ))

                    if is_new_arrival:
                        observations.append(TrendObservation(
                            source_name="ecommerce_scraper",
                            source_type="ecommerce",
                            attribute_type=f"new_arrival_{attr_type}",
                            attribute_value=attr_val,
                            rank_position=rank,
                            collected_at=run_date,
                        ))

                if not any_known_attr:
                    skipped_unmapped_attrs += 1

    print(f"Bulk inserting {len(observations)} trend observation data points...")
    db.bulk_save_objects(observations)
    db.commit()
    db.close()

    print("\n=== Trend Observation Generation Complete ===")
    print(f"Runs processed: {len(run_folders)}")
    print(f"Unique items seen (new arrivals): {len(seen_items)}")
    print(f"Observations generated: {len(observations)}")
    print(f"Skipped (not in Products table): {skipped_unknown_product}")
    print(f"Skipped (all attributes Unknown): {skipped_unmapped_attrs}")


if __name__ == "__main__":
    generate_observations()

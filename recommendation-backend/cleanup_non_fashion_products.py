"""Mark legacy gift-card/voucher catalog rows unavailable.

Usage:
    python cleanup_non_fashion_products.py          # preview
    python cleanup_non_fashion_products.py --apply  # persist
"""

import argparse

from app.database import SessionLocal
from app.models.product import Product
from app.services.product_quality_service import is_non_fashion_product


def cleanup(apply_changes: bool = False) -> int:
    db = SessionLocal()
    try:
        matches = [
            product
            for product in db.query(Product).all()
            if is_non_fashion_product(product)
        ]
        for product in matches:
            print(f"{product.item_id}: {product.title}")
            if apply_changes:
                product.availability = False

        if apply_changes:
            db.commit()
        else:
            db.rollback()

        action = "Marked unavailable" if apply_changes else "Would mark unavailable"
        print(f"{action}: {len(matches)} product(s).")
        return len(matches)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    cleanup(apply_changes=args.apply)

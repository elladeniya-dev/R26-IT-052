"""
Backfills the V2 FashionCLIP image embedding for every product that is
missing one (see app/s_models.py:Product.image_embedding).

The V2 outfit transformer (app/ml_v2/) scores outfits from 512-dim
FashionCLIP embeddings, not raw images. Computing that embedding needs
a ~600MB model download and a CLIP forward pass per image, which is far
too slow to do on every /outfits/generate request - so it is computed
once here and cached in the database instead. Re-run this whenever new
products are synced in (e.g. after scripts/s_sync_koji_products.py).

Usage:
    python scripts/s_generate_embeddings.py
"""

from pathlib import Path
import sys

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from app.s_database import SessionLocal  # noqa: E402
from app.s_models import Product  # noqa: E402
from app.ml_v2.fashionclip_encoder import FashionCLIPEncoder  # noqa: E402

BATCH_SIZE = 16


def backfill_embeddings() -> None:
    db = SessionLocal()

    try:
        products = [
            {
                "item_id": item_id,
                "image_url": image_url,
            }
            for item_id, image_url in db.query(
                Product.item_id,
                Product.image_url,
            )
            .filter(
                Product.image_embedding.is_(None),
                Product.image_url.isnot(None),
            )
            .all()
        ]
    finally:
        # Do not hold a database connection while downloading images or
        # running FashionCLIP inference; both can take long enough for the
        # server to close an idle transaction.
        db.close()

    print(f"{len(products)} products need an embedding.")

    if not products:
        return

    print("Loading FashionCLIP encoder (first run downloads ~600MB)...")
    encoder = FashionCLIPEncoder()

    encoded = 0
    failed = 0

    for start_index in range(0, len(products), BATCH_SIZE):
        batch = products[start_index:start_index + BATCH_SIZE]
        images = []
        image_products = []

        for product in batch:
            try:
                images.append(encoder.load_image(product["image_url"]))
                image_products.append(product)
            except Exception as error:
                failed += 1
                print(f"  skip {product['item_id']}: {error}")

        encoded_products = []
        if images:
            try:
                embeddings = encoder.encode_images(images)
                encoded_products = [
                    (product, embedding.tolist())
                    for product, embedding in zip(image_products, embeddings)
                ]
            except Exception:
                # Keep a single bad image or processor edge case from
                # preventing other products in this batch from being saved.
                for product, image in zip(image_products, images):
                    try:
                        embedding = encoder.encode_images([image])[0].tolist()
                        encoded_products.append((product, embedding))
                    except Exception as item_error:
                        failed += 1
                        print(f"  skip {product['item_id']}: {item_error or error}")

        if encoded_products:
            db = SessionLocal()
            try:
                saved_count = 0
                for product, embedding in encoded_products:
                    stored_product = (
                        db.query(Product)
                        .filter(Product.item_id == product["item_id"])
                        .first()
                    )
                    if (
                        stored_product is None
                        or stored_product.image_url != product["image_url"]
                    ):
                        continue

                    stored_product.image_embedding = embedding
                    saved_count += 1

                db.commit()
                encoded += saved_count
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        print(
            "  progress: "
            f"{min(start_index + BATCH_SIZE, len(products))}/{len(products)}"
        )

    print(f"Done. Encoded {encoded}, failed {failed}.")


if __name__ == "__main__":
    backfill_embeddings()

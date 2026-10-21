from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product


router = APIRouter()


# ============================================================
# SAMPLE PRODUCTS
# ============================================================

@router.post("/products/sample")
def create_sample_products(
    db: Session = Depends(get_db),
):
    """
    Sample products used to test Chala's Learning Engine.

    Later Koji provides real products.
    """

    sample_products = [

        Product(
            item_id="P001",
            product_name="White Cotton T-Shirt",
            category="Tops",
            color=["White"],
            style=["Casual"],
            brand="Gflock",
            occasions=[
                "Daily wear",
                "University / college",
                "Casual outing",
            ],
            product_url=(
                "https://example.com/products/P001"
            ),
            image_url=(
                "https://images.unsplash.com/"
                "photo-1521572163474-6864f9cf17ab"
                "?auto=format&fit=crop&w=900&q=80"
            ),
        ),

        Product(
            item_id="P002",
            product_name="Grey Hoodie",
            category="Hoodies",
            color=["Grey"],
            style=["Comfort"],
            brand="Carnage",
            occasions=[
                "Daily wear",
                "University / college",
                "Travel",
            ],
            product_url=(
                "https://example.com/products/P002"
            ),
            image_url=(
                "https://images.unsplash.com/"
                "photo-1556821840-3a63f95609a7"
                "?auto=format&fit=crop&w=900&q=80"
            ),
        ),

        Product(
            item_id="P003",
            product_name="Blue Denim Jeans",
            category="Jeans",
            color=["Blue"],
            style=["Trendy"],
            brand="Kelly Felder",
            occasions=[
                "Daily wear",
                "Casual outing",
                "Travel",
            ],
            product_url=(
                "https://example.com/products/P003"
            ),
            image_url=(
                "https://images.unsplash.com/"
                "photo-1542272604-787c3835535d"
                "?auto=format&fit=crop&w=900&q=80"
            ),
        ),

        Product(
            item_id="P004",
            product_name="Black Blazer",
            category="Blazers",
            color=["Black"],
            style=["Formal"],
            brand="Gflock",
            occasions=[
                "Office / work",
                "Special events",
            ],
            product_url=(
                "https://example.com/products/P004"
            ),
            image_url=(
                "https://images.unsplash.com/"
                "photo-1592878904946-b3cd8ae243d0"
                "?auto=format&fit=crop&w=900&q=80"
            ),
        ),

        Product(
            item_id="P005",
            product_name="Pink Party Skirt",
            category="Skirts",
            color=["Pink"],
            style=["Party wear"],
            brand="Kelly Felder",
            occasions=[
                "Party",
                "Special events",
            ],
            product_url=(
                "https://example.com/products/P005"
            ),
            image_url=(
                "https://images.unsplash.com/"
                "photo-1583496661160-fb5886a13d44"
                "?auto=format&fit=crop&w=900&q=80"
            ),
        ),
    ]

    inserted_count = 0
    skipped_count = 0

    for product in sample_products:

        existing_product = (
            db.query(Product)
            .filter(
                Product.item_id
                == product.item_id
            )
            .first()
        )

        if existing_product:

            existing_product.product_name = (
                product.product_name
            )

            existing_product.category = (
                product.category
            )

            existing_product.color = (
                product.color
            )

            existing_product.style = (
                product.style
            )

            existing_product.brand = (
                product.brand
            )

            existing_product.occasions = (
                product.occasions
            )

            existing_product.product_url = (
                product.product_url
            )

            existing_product.image_url = (
                product.image_url
            )

            skipped_count += 1
            continue

        db.add(product)
        inserted_count += 1

    db.commit()

    return {
        "message":
            "Sample products processed successfully",

        "inserted_count":
            inserted_count,

        "skipped_count":
            skipped_count,
    }
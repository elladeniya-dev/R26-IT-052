from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("")
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()

    return {
        "total_products": len(products),
        "products": [
            {
                "item_id": product.item_id,
                "title": product.title,
                "category": product.category,
                "subcategory": product.subcategory,
                "color": product.color,
                "style": product.style,
                "brand": product.brand,
                "price": product.price,
                "currency": product.currency,
                "image_url": product.image_url,
                "product_url": product.product_url,
                "availability": product.availability
            }
            for product in products
        ]
    }
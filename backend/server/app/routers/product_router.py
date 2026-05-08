from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("")
def get_all_products(db: Session = Depends(get_db)):
    try:
        products = db.query(models.Product).all()

        return {
            "status": "success",
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
                    "source": product.source,
                    "description": product.description,
                    "availability": product.availability,
                    "collected_at": product.collected_at.isoformat() if product.collected_at else None
                }
                for product in products
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve products: {str(e)}"
        )


@router.get("/{item_id}")
def get_product_by_id(
    item_id: str,
    db: Session = Depends(get_db)
):
    try:
        if not item_id or not item_id.strip():
            raise HTTPException(
                status_code=400,
                detail="item_id cannot be empty"
            )

        cleaned_item_id = item_id.strip()

        product = db.query(models.Product).filter(
            models.Product.item_id == cleaned_item_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        return {
            "status": "success",
            "product": {
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
                "source": product.source,
                "description": product.description,
                "availability": product.availability,
                "collected_at": product.collected_at.isoformat() if product.collected_at else None
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve product: {str(e)}"
        )
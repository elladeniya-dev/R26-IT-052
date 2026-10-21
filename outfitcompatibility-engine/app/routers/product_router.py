from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.s_database import get_db
from app import s_models
from app.s_product_filters import apply_real_product_filter


def product_to_response(product: s_models.Product):
    return {
        "item_id": product.item_id,
        "title": product.title,
        "role": product.category,
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


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("")
def get_all_products(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    try:
        product_query = apply_real_product_filter(db.query(s_models.Product))
        total_products = product_query.count()
        products = (
            product_query
            .order_by(s_models.Product.collected_at.desc(), s_models.Product.item_id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "status": "success",
            "total_products": total_products,
            "limit": limit,
            "offset": offset,
            "products": [
                product_to_response(product)
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

        product = apply_real_product_filter(db.query(s_models.Product)).filter(
            s_models.Product.item_id == cleaned_item_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        return {
            "status": "success",
            "product": product_to_response(product)
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve product: {str(e)}"
        )

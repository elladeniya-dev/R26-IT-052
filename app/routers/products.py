from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db

router = APIRouter(tags=["Products & Metrics"])


@router.get("/products/")
def get_all_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    total_products = db.query(models.Product).count()

    return {
        "total_products": total_products,
        "returned_count": len(products),
        "products": products,
    }


@router.get("/products/new-arrivals", response_model=schemas.NewArrivalsResponse)
def get_new_arrivals(hours: int = 48, limit: int = 50, db: Session = Depends(get_db)):
    """Products first seen within the last `hours` — genuinely new, not just recently updated."""
    latest_collected = db.query(func.max(models.Product.collected_at)).scalar()
    if not latest_collected:
        return {"total": 0, "items": []}

    cutoff = latest_collected - timedelta(hours=hours)
    products = (
        db.query(models.Product)
        .filter(models.Product.collected_at >= cutoff)
        .order_by(models.Product.collected_at.desc())
        .limit(limit)
        .all()
    )
    return {"total": len(products), "items": products}


@router.get("/products/on-sale", response_model=schemas.DiscountedItemsResponse)
def get_discounted_products(min_discount_pct: float = 5.0, limit: int = 50, db: Session = Depends(get_db)):
    """Products currently marked down (original_price > price), ranked by discount size."""
    discount_pct_expr = (
        100 * (models.Product.original_price - models.Product.price) / models.Product.original_price
    )
    products = (
        db.query(models.Product, discount_pct_expr.label("discount_pct"))
        .filter(
            models.Product.original_price.isnot(None),
            models.Product.original_price > 0,
            models.Product.original_price > models.Product.price,
            discount_pct_expr >= min_discount_pct,
        )
        .order_by(discount_pct_expr.desc())
        .limit(limit)
        .all()
    )

    items = [
        {
            "item_id": p.item_id,
            "title": p.title,
            "brand": p.brand,
            "category": p.category,
            "price": p.price,
            "original_price": p.original_price,
            "discount_pct": round(discount_pct, 1),
            "availability": p.availability,
            "image_url": p.image_url,
            "product_url": p.product_url,
        }
        for p, discount_pct in products
    ]
    return {"total": len(items), "items": items}


@router.get("/product-metrics/")
def get_all_product_metrics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    metrics = db.query(models.ProductTrendMetric).offset(skip).limit(limit).all()
    total_metrics = db.query(models.ProductTrendMetric).count()

    return {
        "total_metrics": total_metrics,
        "returned_count": len(metrics),
        "metrics": metrics,
    }

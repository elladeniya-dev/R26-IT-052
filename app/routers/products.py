from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db

router = APIRouter(tags=["Products & Metrics"])


@router.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    existing_product = (
        db.query(models.Product)
        .filter(models.Product.item_id == product.item_id)
        .first()
    )

    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product with this item_id already exists",
        )

    new_product = models.Product(
        item_id=product.item_id,
        title=product.title,
        category=product.category,
        subcategory=product.subcategory,
        color=product.color,
        style=product.style,
        brand=product.brand,
        price=product.price,
        currency=product.currency,
        material=product.material,
        pattern=product.pattern,
        fit_type=product.fit_type,
        target_gender=product.target_gender,
        image_url=product.image_url,
        product_url=product.product_url,
        source=product.source,
        description=product.description,
        availability=product.availability,
        collected_at=product.collected_at,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


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
    products = (
        db.query(models.Product)
        .filter(
            models.Product.original_price.isnot(None),
            models.Product.original_price > models.Product.price,
        )
        .all()
    )

    items = []
    for p in products:
        discount_pct = round(100 * (p.original_price - p.price) / p.original_price, 1)
        if discount_pct >= min_discount_pct:
            items.append({
                "item_id": p.item_id,
                "title": p.title,
                "brand": p.brand,
                "category": p.category,
                "price": p.price,
                "original_price": p.original_price,
                "discount_pct": discount_pct,
                "availability": p.availability,
                "image_url": p.image_url,
                "product_url": p.product_url,
            })

    items.sort(key=lambda x: x["discount_pct"], reverse=True)
    items = items[:limit]
    return {"total": len(items), "items": items}


@router.post("/product-metrics/", response_model=schemas.ProductTrendMetricResponse)
def create_product_metric(
    metric: schemas.ProductTrendMetricCreate,
    db: Session = Depends(get_db),
):
    product = (
        db.query(models.Product)
        .filter(models.Product.item_id == metric.item_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found. Add product before adding trend metrics.",
        )

    new_metric = models.ProductTrendMetric(
        item_id=metric.item_id,
        view_count=metric.view_count,
        wishlist_count=metric.wishlist_count,
        sales_volume=metric.sales_volume,
        social_mentions=metric.social_mentions,
        availability=metric.availability,
        recorded_at=metric.recorded_at,
    )

    db.add(new_metric)
    db.commit()
    db.refresh(new_metric)

    return new_metric


@router.get("/product-metrics/")
def get_all_product_metrics(db: Session = Depends(get_db)):
    metrics = db.query(models.ProductTrendMetric).all()

    return {
        "total_metrics": len(metrics),
        "metrics": metrics,
    }

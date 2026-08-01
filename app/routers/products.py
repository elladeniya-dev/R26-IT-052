from fastapi import APIRouter, Depends, HTTPException
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
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()

    return {
        "total_products": len(products),
        "products": products,
    }


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

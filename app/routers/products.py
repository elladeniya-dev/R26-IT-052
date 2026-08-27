from fastapi import APIRouter, Depends, HTTPException
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


@router.get("/product-metrics/")
def get_all_product_metrics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    metrics = db.query(models.ProductTrendMetric).offset(skip).limit(limit).all()
    total_metrics = db.query(models.ProductTrendMetric).count()

    return {
        "total_metrics": total_metrics,
        "returned_count": len(metrics),
        "metrics": metrics,
    }

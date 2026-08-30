from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.product import AttributeOut, ProductHistoryResponse, ProductResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("")
def list_products(
    brand: str | None = None,
    category: str | None = None,
    color: str | None = None,
    fabric: str | None = None,
    on_sale: bool | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    products, total = ProductService(db).list_products(
        brand_slug=brand, category=category, color=color, fabric=fabric,
        on_sale=on_sale, page=page, size=size,
    )
    data = [ProductResponse.model_validate(p, from_attributes=True) for p in products]
    return {"data": data, "meta": {"page": page, "size": size, "total": total}}


@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    product, attributes = ProductService(db).get_product(product_id)
    out = ProductResponse.model_validate(product, from_attributes=True)
    out.attributes = [AttributeOut.model_validate(a, from_attributes=True) for a in attributes]
    return {"data": out}


@router.get("/{product_id}/history")
def get_product_history(product_id: str, db: Session = Depends(get_db)):
    result = ProductService(db).get_history(product_id)
    return {"data": ProductHistoryResponse.model_validate(result, from_attributes=True)}

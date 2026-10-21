from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.schemas.product_schema import ProductCreate, ProductResponse
from app.services.fashion_attribute_normalizer import (
    canonicalize_attribute,
    tokenize_attribute_values,
)
from app.services.product_quality_service import is_non_fashion_product

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post("/", response_model=ProductResponse)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    if is_non_fashion_product(product_data):
        raise HTTPException(
            status_code=422,
            detail="Gift cards, vouchers, and store credit are not fashion products",
        )
    existing_product = (
        db.query(Product)
        .filter(Product.item_id == product_data.item_id)
        .first()
    )

    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product with this item_id already exists",
        )

    normalized_data = product_data.model_dump()
    normalized_data["category"] = canonicalize_attribute(
        normalized_data.get("category"), "category"
    ) or "unknown"
    normalized_data["subcategory"] = canonicalize_attribute(
        normalized_data.get("subcategory"), "category"
    ) or normalized_data["category"]
    normalized_data["color"] = tokenize_attribute_values(
        normalized_data.get("color"), "color"
    )
    normalized_data["style"] = tokenize_attribute_values(
        normalized_data.get("style"), "style"
    )
    normalized_data["brand"] = canonicalize_attribute(
        normalized_data.get("brand"), "brand"
    ) or None
    new_product = Product(**normalized_data)

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@router.get("/", response_model=list[ProductResponse])
def get_all_products(db: Session = Depends(get_db)):
    """
    Returns only currently available products.

    This prevents old, hidden, sample, or out-of-stock products from
    appearing in the product listing API.
    """

    products = (
        db.query(Product)
        .filter(Product.availability.is_(True))
        .order_by(Product.source, Product.category, Product.title)
        .all()
    )

    return [product for product in products if not is_non_fashion_product(product)]

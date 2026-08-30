from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.run_repo import RunRepository
from app.schemas.brand import BrandCoverageResponse, BrandResponse, CoverageDay
from app.services.product_service import ProductService

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("")
def list_brands(db: Session = Depends(get_db)):
    brands = ProductService(db).list_brands()
    data = [BrandResponse.model_validate(b, from_attributes=True) for b in brands]
    return {"data": data, "meta": {"total": len(data)}}


@router.get("/{slug}/coverage")
def get_coverage(slug: str, db: Session = Depends(get_db)):
    brand = ProductService(db).get_brand(slug)  # raises BrandNotFoundError if missing
    runs = RunRepository(db).get_brand_coverage(brand.brand_id)
    result = BrandCoverageResponse(
        brand=BrandResponse.model_validate(brand, from_attributes=True),
        days=[
            CoverageDay(
                run_date=r.run_date, status=r.status,
                products_seen=r.products_seen, products_kept=r.products_kept,
            )
            for r in runs
        ],
    )
    return {"data": result}

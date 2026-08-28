from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.core.database import get_db
from app.core.koji_database import get_koji_db
from app.services.trending_service import get_trending_products

router = APIRouter(tags=["Trending"])


@router.get("/trending-products/", response_model=schemas.TrendingProductsResponse)
def get_trending(
    limit: int = 20,
    db: Session = Depends(get_db),
    koji_db: Session = Depends(get_koji_db),
):
    """
    Koji catalog products whose category or color is currently flagged
    rising in our own TrendSignal data. No user preferences involved —
    see app/services/trending_service.py.
    """
    products = get_trending_products(db=db, koji_db=koji_db, limit=limit)
    return {"total": len(products), "products": products}

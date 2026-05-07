from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.crawler_schema import CrawlRequest, CrawlResponse
from app.services.crawler_service import (
    generate_sample_crawled_products,
    save_crawled_products
)

router = APIRouter(
    prefix="/crawler",
    tags=["Crawler"]
)


@router.post("/run", response_model=CrawlResponse)
def run_crawler(
    request: CrawlRequest,
    db: Session = Depends(get_db)
):
    crawled_products = generate_sample_crawled_products(request)

    inserted_count, skipped_count, updated_count = save_crawled_products(
        db=db,
        products=crawled_products
    )

    return {
        "message": f"Crawler completed successfully. Updated {updated_count} existing products.",
        "inserted_count": inserted_count,
        "skipped_count": skipped_count
    }
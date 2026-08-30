from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    brand_id: int
    slug: str
    display_name: str
    base_url: str | None
    source_tier: int
    market_segment: str | None
    is_active: bool
    created_at: datetime


class CoverageDay(BaseModel):
    run_date: date
    status: str
    products_seen: int
    products_kept: int


class BrandCoverageResponse(BaseModel):
    brand: BrandResponse
    days: list[CoverageDay]

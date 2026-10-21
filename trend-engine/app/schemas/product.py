from datetime import date

from pydantic import BaseModel, ConfigDict


class AttributeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attr_type: str
    attr_value: str
    is_primary: bool


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    brand_id: int
    title: str
    category: str
    raw_product_type: str | None
    product_url: str | None
    image_url: str | None
    published_date: date | None
    source_tier: int
    first_seen: date
    attributes: list[AttributeOut] = []


class PriceHistoryPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    obs_date: date
    price_lkr: float | None
    compare_at_lkr: float | None
    is_on_sale: bool
    in_stock: bool | None
    rank_position: int | None


class ProductHistoryResponse(BaseModel):
    product_id: str
    first_seen: date
    last_seen: date | None
    is_still_listed: bool
    history: list[PriceHistoryPoint]

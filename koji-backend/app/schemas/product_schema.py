from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ProductCreate(BaseModel):
    item_id: str
    title: str
    category: str
    subcategory: Optional[str] = None
    color: List[str]
    style: List[str]
    brand: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "LKR"
    image_url: str
    product_url: str
    source: str
    description: Optional[str] = None
    availability: Optional[bool] = True


class ProductResponse(ProductCreate):
    collected_at: datetime

    class Config:
        from_attributes = True
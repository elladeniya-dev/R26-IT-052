from pydantic import BaseModel
from typing import List, Optional


class CrawlRequest(BaseModel):
    category: Optional[str] = None
    colors: Optional[List[str]] = []
    styles: Optional[List[str]] = []
    max_items: Optional[int] = 10


class CrawlResponse(BaseModel):
    message: str
    inserted_count: int
    skipped_count: int
    
from typing import Optional
from pydantic import BaseModel, Field


class OutfitGenerateRequest(BaseModel):
    user_id: str = Field(..., example="USR001")
    selected_item_id: str = Field(..., example="P001")
    occasion: Optional[str] = Field(default="casual", example="casual")
    max_outfits: Optional[int] = Field(default=5, example=5)
from typing import Optional
from pydantic import BaseModel, Field, field_validator


ALLOWED_OCCASIONS = ["casual", "office", "formal", "party", "sports"]


class OutfitGenerateRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=1,
        example="USR001"
    )

    selected_item_id: str = Field(
        ...,
        min_length=1,
        example="P001"
    )

    occasion: Optional[str] = Field(
        default="casual",
        example="casual"
    )

    max_outfits: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        example=5
    )

    @field_validator("user_id", "selected_item_id")
    @classmethod
    def not_empty_string(cls, value):
        if not value or not value.strip():
            raise ValueError("This field cannot be empty")
        return value.strip()

    @field_validator("occasion")
    @classmethod
    def validate_occasion(cls, value):
        if value is None:
            return "casual"

        value = value.strip().lower()

        if value not in ALLOWED_OCCASIONS:
            raise ValueError(
                f"Invalid occasion. Allowed occasions are: {ALLOWED_OCCASIONS}"
            )

        return value
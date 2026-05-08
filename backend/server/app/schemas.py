from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


ALLOWED_OCCASIONS = [
    "casual",
    "office",
    "formal",
    "party",
    "sports"
]


ALLOWED_CATEGORIES = [
    "top",
    "bottom",
    "dress",
    "outerwear",
    "footwear",
    "accessory"
]


class OutfitGenerateRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=1,
        example="USR001",
        description="ID of the user requesting outfit suggestions"
    )

    selected_item_id: str = Field(
        ...,
        min_length=1,
        example="P001",
        description="Item ID selected by the user from Koji's recommendation output"
    )

    occasion: Optional[str] = Field(
        default="casual",
        example="casual",
        description="Occasion type such as casual, office, formal, party, or sports"
    )

    max_outfits: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        example=5,
        description="Maximum number of outfit suggestions to return. Allowed range: 1 to 20"
    )

    min_price: Optional[float] = Field(
        default=None,
        ge=0,
        example=3000,
        description="Minimum product price filter"
    )

    max_price: Optional[float] = Field(
        default=None,
        ge=0,
        example=10000,
        description="Maximum product price filter"
    )

    preferred_colors: Optional[List[str]] = Field(
        default=None,
        example=["black", "white", "blue"],
        description="Preferred colors for outfit items"
    )

    excluded_categories: Optional[List[str]] = Field(
        default=None,
        example=["outerwear"],
        description="Categories to exclude from generated outfits"
    )

    max_items_per_category: Optional[int] = Field(
        default=10,
        ge=1,
        le=50,
        example=10,
        description="Maximum number of products to load from each category"
    )

    @field_validator("user_id", "selected_item_id")
    @classmethod
    def remove_empty_spaces(cls, value: str):
        if not value or not value.strip():
            raise ValueError("This field cannot be empty")
        return value.strip()

    @field_validator("occasion")
    @classmethod
    def validate_occasion(cls, value: Optional[str]):
        if value is None or not value.strip():
            return "casual"

        cleaned_value = value.strip().lower()

        if cleaned_value not in ALLOWED_OCCASIONS:
            raise ValueError(
                f"Invalid occasion. Allowed values are: {', '.join(ALLOWED_OCCASIONS)}"
            )

        return cleaned_value

    @field_validator("preferred_colors")
    @classmethod
    def clean_preferred_colors(cls, value: Optional[List[str]]):
        if not value:
            return None

        cleaned_colors = []

        for color in value:
            if color and color.strip():
                cleaned_colors.append(color.strip().lower())

        return cleaned_colors if cleaned_colors else None

    @field_validator("excluded_categories")
    @classmethod
    def validate_excluded_categories(cls, value: Optional[List[str]]):
        if not value:
            return None

        cleaned_categories = []

        for category in value:
            if category and category.strip():
                cleaned_category = category.strip().lower()

                if cleaned_category not in ALLOWED_CATEGORIES:
                    raise ValueError(
                        f"Invalid category: {cleaned_category}. Allowed categories are: {', '.join(ALLOWED_CATEGORIES)}"
                    )

                cleaned_categories.append(cleaned_category)

        return cleaned_categories if cleaned_categories else None

    @field_validator("max_price")
    @classmethod
    def validate_price_range(cls, max_price, info):
        min_price = info.data.get("min_price")

        if min_price is not None and max_price is not None:
            if max_price < min_price:
                raise ValueError("max_price cannot be less than min_price")

        return max_price
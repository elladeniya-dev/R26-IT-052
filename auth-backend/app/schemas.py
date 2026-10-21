from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.fashion_attribute_normalizer import (
    canonicalize_values,
    canonicalize_weight_map,
)


def _preference_list_validator(field_name: str, value: Any) -> list[str]:
    dimensions = {
        "preferred_categories": "category",
        "categories": "category",
        "preferred_colors": "color",
        "colors": "color",
        "preferred_styles": "style",
        "styles": "style",
        "preferred_brands": "brand",
        "occasions": "occasion",
    }
    return canonicalize_values(value, dimensions[field_name])


def _preference_map_validator(field_name: str, value: Any) -> dict[str, float]:
    dimensions = {
        "category_weights": "category",
        "category_scores": "category",
        "color_weights": "color",
        "color_scores": "color",
        "style_weights": "style",
        "style_scores": "style",
        "brand_weights": "brand",
        "brand_scores": "brand",
        "occasion_weights": "occasion",
        "occasion_scores": "occasion",
    }
    return canonicalize_weight_map(value, dimensions[field_name])


class GoogleLoginRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
    user_id: int
    google_sub: str
    full_name: str
    email: EmailStr
    profile_picture: Optional[str] = None
    auth_provider: str

    class Config:
        from_attributes = True


class GoogleLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class OnboardingRequest(BaseModel):
    preferred_categories: List[str]
    preferred_colors: List[str]
    preferred_styles: List[str]
    occasions: List[str]
    choice_priorities: Optional[List[str]] = None
    preferred_brands: Optional[List[str]] = None
    extra_preferences: Optional[Dict[str, Any]] = None

    @field_validator(
        "preferred_categories", "preferred_colors", "preferred_styles",
        "occasions", "preferred_brands", mode="before",
    )
    @classmethod
    def normalize_preferences(cls, value, info):
        return _preference_list_validator(info.field_name, value)


class OnboardingResponse(BaseModel):
    preference_id: int
    user_id: int
    preferred_categories: List[str]
    preferred_colors: List[str]
    preferred_styles: List[str]
    occasions: List[str]
    choice_priorities: Optional[List[str]] = None
    preferred_brands: Optional[List[str]] = None
    extra_preferences: Optional[Dict[str, Any]] = None

    @field_validator(
        "preferred_categories", "preferred_colors", "preferred_styles",
        "occasions", "preferred_brands", mode="before",
    )
    @classmethod
    def normalize_preferences(cls, value, info):
        return _preference_list_validator(info.field_name, value)

    class Config:
        from_attributes = True


class LearnedPreferenceResponse(BaseModel):
    learned_id: int
    user_id: int

    category_weights: Dict[str, float]
    color_weights: Dict[str, float]
    style_weights: Dict[str, float]

    brand_weights: Optional[
        Dict[str, float]
    ] = None

    # NEW
    occasion_weights: Optional[
        Dict[str, float]
    ] = None

    @field_validator(
        "category_weights", "color_weights", "style_weights",
        "brand_weights", "occasion_weights", mode="before",
    )
    @classmethod
    def normalize_weights(cls, value, info):
        return _preference_map_validator(info.field_name, value)

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    user: UserResponse
    onboarding_preferences: Optional[
        OnboardingResponse
    ] = None
    learned_preferences: Optional[
        LearnedPreferenceResponse
    ] = None


class InteractionRequest(BaseModel):
    item_id: str
    interaction_type: str
    interaction_value: Optional[float] = None


class InteractionResponse(BaseModel):
    interaction_id: int
    user_id: int
    item_id: str
    interaction_type: str
    interaction_value: float

    class Config:
        from_attributes = True


class InteractionHistoryItem(BaseModel):
    interaction_id: int
    item_id: str
    interaction_type: str
    interaction_value: float
    created_at: datetime

    product_name: Optional[str] = None
    category: Optional[str] = None
    color: Optional[List[str]] = None
    style: Optional[List[str]] = None
    brand: Optional[str] = None

    # NEW
    occasions: Optional[List[str]] = None

    image_url: Optional[str] = None
    product_url: Optional[str] = None


class InteractionStatsResponse(BaseModel):
    total_interactions: int
    view_count: int
    click_count: int
    save_count: int
    select_count: int
    dislike_count: int


class InteractionHistoryResponse(BaseModel):
    stats: InteractionStatsResponse
    interactions: List[InteractionHistoryItem]


class CurrentPreferencesResponse(BaseModel):
    category_scores: Dict[str, float]
    color_scores: Dict[str, float]
    style_scores: Dict[str, float]

    # Keep dynamic Brand
    brand_scores: Dict[str, float]

    # NEW dynamic Occasion
    occasion_scores: Dict[str, float]

    @field_validator(
        "category_scores", "color_scores", "style_scores",
        "brand_scores", "occasion_scores", mode="before",
    )
    @classmethod
    def normalize_scores(cls, value, info):
        return _preference_map_validator(info.field_name, value)


class MLExpansionItem(BaseModel):
    model_feature: str
    preference: str
    probability: float
    uplift: float
    ranking_method: str


class PreferenceValuesResponse(BaseModel):
    preferred_colors: List[str]
    preferred_categories: List[str]
    preferred_styles: List[str]
    occasions: List[str]
    choice_priorities: List[str]
    preferred_brands: List[str]

    @field_validator(
        "preferred_colors", "preferred_categories", "preferred_styles",
        "occasions", "preferred_brands", mode="before",
    )
    @classmethod
    def normalize_preferences(cls, value, info):
        return _preference_list_validator(info.field_name, value)


class MLExpansionGroupsResponse(BaseModel):
    colors: List[MLExpansionItem]
    categories: List[MLExpansionItem]
    styles: List[MLExpansionItem]
    occasions: List[MLExpansionItem]


class PreferenceExpansionResponse(BaseModel):
    original_preferences: PreferenceValuesResponse
    ml_expansions: MLExpansionGroupsResponse
    enriched_preferences: PreferenceValuesResponse


class EnrichedCurrentPreferencesResponse(BaseModel):
    current_preferences: CurrentPreferencesResponse
    ml_expansions: MLExpansionGroupsResponse
    enriched_preferences: PreferenceValuesResponse



class IntegrationEnrichedPreferencesResponse(BaseModel):
    user_id: int
    categories: list[str]
    colors: list[str]
    styles: list[str]
    occasions: list[str]
    preferred_brands: list[str]
    category_weights: Dict[str, float]
    color_weights: Dict[str, float]
    style_weights: Dict[str, float]
    brand_weights: Dict[str, float]
    occasion_weights: Dict[str, float]
    preference_sources: Dict[str, Dict[str, List[str]]]

    @field_validator(
        "categories", "colors", "styles", "occasions",
        "preferred_brands", mode="before",
    )
    @classmethod
    def normalize_preferences(cls, value, info):
        return _preference_list_validator(info.field_name, value)

    @field_validator(
        "category_weights", "color_weights", "style_weights",
        "brand_weights", "occasion_weights", mode="before",
    )
    @classmethod
    def normalize_weights(cls, value, info):
        return _preference_map_validator(info.field_name, value)

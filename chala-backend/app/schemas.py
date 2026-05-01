from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any


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
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    occasions: List[str]
    preferred_patterns: Optional[List[str]] = None
    extra_preferences: Optional[Dict[str, Any]] = None


class OnboardingResponse(BaseModel):
    preference_id: int
    user_id: int
    preferred_categories: List[str]
    preferred_colors: List[str]
    preferred_styles: List[str]
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    occasions: List[str]
    preferred_patterns: Optional[List[str]] = None
    extra_preferences: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class LearnedPreferenceResponse(BaseModel):
    learned_id: int
    user_id: int
    category_weights: Dict[str, float]
    color_weights: Dict[str, float]
    style_weights: Dict[str, float]
    brand_weights: Optional[Dict[str, float]] = None

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    user: UserResponse
    onboarding_preferences: Optional[OnboardingResponse] = None
    learned_preferences: Optional[LearnedPreferenceResponse] = None


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





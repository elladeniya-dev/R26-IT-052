from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    User,
    UserOnboardingPreference,
)

from app.schemas import (
    OnboardingRequest,
    OnboardingResponse,
)

from app.auth import get_current_user


router = APIRouter()


# ============================================================
# ONBOARDING
# ============================================================

@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
)
def save_onboarding_preferences(
    request: OnboardingRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Saves or updates onboarding preferences.
    """

    existing_preferences = (
        db.query(
            UserOnboardingPreference
        )
        .filter(
            UserOnboardingPreference.user_id
            == current_user.user_id
        )
        .first()
    )

    if existing_preferences:

        existing_preferences.preferred_categories = (
            request.preferred_categories
        )

        existing_preferences.preferred_colors = (
            request.preferred_colors
        )

        existing_preferences.preferred_styles = (
            request.preferred_styles
        )

        existing_preferences.occasions = (
            request.occasions
        )

        existing_preferences.choice_priorities = (
            request.choice_priorities
        )

        existing_preferences.preferred_brands = (
            request.preferred_brands
        )

        existing_preferences.extra_preferences = (
            request.extra_preferences
        )

        db.commit()
        db.refresh(
            existing_preferences
        )

        return existing_preferences


    new_preferences = UserOnboardingPreference(
        user_id=current_user.user_id,

        preferred_categories=(
            request.preferred_categories
        ),

        preferred_colors=(
            request.preferred_colors
        ),

        preferred_styles=(
            request.preferred_styles
        ),

        price_min=None,
        price_max=None,

        occasions=(
            request.occasions
        ),

        choice_priorities=(
            request.choice_priorities
        ),

        preferred_brands=(
            request.preferred_brands
        ),

        extra_preferences=(
            request.extra_preferences
        ),
    )

    db.add(new_preferences)
    db.commit()
    db.refresh(new_preferences)

    return new_preferences
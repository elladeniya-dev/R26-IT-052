from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    User,
    UserOnboardingPreference,
)

from app.schemas import (
    PreferenceExpansionResponse,
)

from app.auth import get_current_user

from app.ml.preference_expansion_service import (
    expand_onboarding_preferences,
)


router = APIRouter()


# ============================================================
# LOGISTIC REGRESSION PREFERENCE EXPANSION
# ============================================================

@router.get(
    "/ml/preference-expansion",
    response_model=PreferenceExpansionResponse,
)
def get_ml_preference_expansion(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Runs the trained Logistic Regression
    co-preference expansion model.
    """

    onboarding_preferences = (
        db.query(
            UserOnboardingPreference
        )
        .filter(
            UserOnboardingPreference.user_id
            == current_user.user_id
        )
        .first()
    )

    if not onboarding_preferences:

        raise HTTPException(
            status_code=404,
            detail=(
                "No onboarding preferences "
                "found for this user"
            ),
        )

    return expand_onboarding_preferences(

        preferred_colors=(
            onboarding_preferences
            .preferred_colors
        ),

        preferred_categories=(
            onboarding_preferences
            .preferred_categories
        ),

        preferred_styles=(
            onboarding_preferences
            .preferred_styles
        ),

        occasions=(
            onboarding_preferences
            .occasions
        ),

        choice_priorities=(
            onboarding_preferences
            .choice_priorities
        ),

        preferred_brands=(
            onboarding_preferences
            .preferred_brands
        ),
    )



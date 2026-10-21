from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User,
    UserLearnedPreference,
    UserOnboardingPreference,
)

from app.schemas import (
    IntegrationEnrichedPreferencesResponse,
)

from app.routes.profile_routes import (
    get_enriched_current_preferences,
)
from app.services.preference_metadata_service import (
    build_weighted_preference_metadata,
)
from app.services.fashion_attribute_normalizer import canonicalize_values


router = APIRouter(
    prefix="/integration",
    tags=["Integration"],
)


@router.get(
    "/users/{user_id}/enriched-preferences",
    response_model=IntegrationEnrichedPreferencesResponse,
)
def get_user_enriched_preferences_for_integration(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Backend-to-backend endpoint for Koji's
    Recommendation Engine.

    Returns the final enriched preference profile
    for the requested user_id.
    """

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    result = (
        get_enriched_current_preferences(
            current_user=user,
            db=db,
        )
    )

    enriched = (
        result.get(
            "enriched_preferences",
            {},
        )
        or {}
    )

    flat_preferences = {
        "categories": canonicalize_values(
            enriched.get("preferred_categories", []), "category"
        ),
        "colors": canonicalize_values(enriched.get("preferred_colors", []), "color"),
        "styles": canonicalize_values(enriched.get("preferred_styles", []), "style"),
        "occasions": canonicalize_values(enriched.get("occasions", []), "occasion"),
        "preferred_brands": canonicalize_values(
            enriched.get("preferred_brands", []), "brand"
        ),
    }

    onboarding_preferences = (
        db.query(UserOnboardingPreference)
        .filter(UserOnboardingPreference.user_id == user_id)
        .first()
    )
    learned_preferences = (
        db.query(UserLearnedPreference)
        .filter(UserLearnedPreference.user_id == user_id)
        .first()
    )

    explicit_preferences = {
        "categories": getattr(
            onboarding_preferences, "preferred_categories", None
        ) or [],
        "colors": getattr(onboarding_preferences, "preferred_colors", None) or [],
        "styles": getattr(onboarding_preferences, "preferred_styles", None) or [],
        "occasions": getattr(onboarding_preferences, "occasions", None) or [],
        "preferred_brands": getattr(
            onboarding_preferences, "preferred_brands", None
        ) or [],
    }
    learned_weight_values = {
        "category_weights": getattr(
            learned_preferences, "category_weights", None
        ) or {},
        "color_weights": getattr(learned_preferences, "color_weights", None) or {},
        "style_weights": getattr(learned_preferences, "style_weights", None) or {},
        "brand_weights": getattr(learned_preferences, "brand_weights", None) or {},
        "occasion_weights": getattr(
            learned_preferences, "occasion_weights", None
        ) or {},
    }
    metadata = build_weighted_preference_metadata(
        flat_preferences=flat_preferences,
        explicit_preferences=explicit_preferences,
        learned_weights=learned_weight_values,
        ml_expansions=result.get("ml_expansions", {}) or {},
    )

    return {
        "user_id":
            user.user_id,

        "categories": flat_preferences["categories"],

        "colors": flat_preferences["colors"],

        "styles": flat_preferences["styles"],

        "occasions": flat_preferences["occasions"],

        "preferred_brands": flat_preferences["preferred_brands"],
        **metadata,
    }

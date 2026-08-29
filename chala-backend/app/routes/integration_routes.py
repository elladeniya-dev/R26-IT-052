from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

from app.schemas import (
    IntegrationEnrichedPreferencesResponse,
)

from app.routes.profile_routes import (
    get_enriched_current_preferences,
)


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

    return {
        "user_id":
            user.user_id,

        "categories":
            enriched.get(
                "preferred_categories",
                [],
            )
            or [],

        "colors":
            enriched.get(
                "preferred_colors",
                [],
            )
            or [],

        "styles":
            enriched.get(
                "preferred_styles",
                [],
            )
            or [],

        "occasions":
            enriched.get(
                "occasions",
                [],
            )
            or [],

        "preferred_brands":
            enriched.get(
                "preferred_brands",
                [],
            )
            or [],
    }

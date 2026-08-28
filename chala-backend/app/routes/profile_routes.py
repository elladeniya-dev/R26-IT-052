from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import defaultdict
from app.database import get_db

from app.models import (
    User,
    UserOnboardingPreference,
    UserLearnedPreference,
    UserInteraction,
    Product,
)

from app.schemas import (
    ProfileResponse,
    CurrentPreferencesResponse,
    EnrichedCurrentPreferencesResponse,
)

from app.learning_engine import calculate_learned_preferences

from app.services.current_preference_service import (
    get_onboarding_weight,
    combine_current_preferences,
)

from app.ml.preference_expansion_service import (
    expand_onboarding_preferences,
)

from app.auth import get_current_user


router = APIRouter()


# ============================================================
# PROFILE
# ============================================================

@router.get(
    "/profile",
    response_model=ProfileResponse,
)
def get_profile(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Returns user profile,
    onboarding preferences,
    and learned preferences.
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

    learned_preferences = (
        db.query(
            UserLearnedPreference
        )
        .filter(
            UserLearnedPreference.user_id
            == current_user.user_id
        )
        .first()
    )

    return {
        "user":
            current_user,

        "onboarding_preferences":
            onboarding_preferences,

        "learned_preferences":
            learned_preferences,
    }


# ============================================================
# CURRENT PREFERENCES
# ============================================================

@router.get(
    "/profile/current-preferences",
    response_model=CurrentPreferencesResponse,
)
def get_current_preferences(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Returns the user's current dynamic fashion profile.
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

    interactions = (
        db.query(
            UserInteraction
        )
        .filter(
            UserInteraction.user_id
            == current_user.user_id
        )
        .all()
    )

    interaction_count = len(
        interactions
    )

    learned_data = {
        "category_weights": {},
        "color_weights": {},
        "style_weights": {},
        "brand_weights": {},
        "occasion_weights": {},
    }

    if interactions:

        item_ids = [
            interaction.item_id
            for interaction
            in interactions
        ]

        products = (
            db.query(Product)
            .filter(
                Product.item_id.in_(
                    item_ids
                )
            )
            .all()
        )

        products_by_id = {
            product.item_id:
                product
            for product
            in products
        }

        learned_data = (
            calculate_learned_preferences(
                interactions=interactions,
                products_by_id=products_by_id,
            )
        )

        learned_preferences = (
            db.query(
                UserLearnedPreference
            )
            .filter(
                UserLearnedPreference.user_id
                == current_user.user_id
            )
            .first()
        )

        if learned_preferences:

            learned_preferences.category_weights = (
                learned_data["category_weights"]
            )

            learned_preferences.color_weights = (
                learned_data["color_weights"]
            )

            learned_preferences.style_weights = (
                learned_data["style_weights"]
            )

            learned_preferences.brand_weights = (
                learned_data["brand_weights"]
            )

            learned_preferences.occasion_weights = (
                learned_data["occasion_weights"]
            )

        else:

            learned_preferences = (
                UserLearnedPreference(
                    user_id=current_user.user_id,

                    category_weights=(
                        learned_data[
                            "category_weights"
                        ]
                    ),

                    color_weights=(
                        learned_data[
                            "color_weights"
                        ]
                    ),

                    style_weights=(
                        learned_data[
                            "style_weights"
                        ]
                    ),

                    brand_weights=(
                        learned_data[
                            "brand_weights"
                        ]
                    ),

                    occasion_weights=(
                        learned_data[
                            "occasion_weights"
                        ]
                    ),
                )
            )

            db.add(
                learned_preferences
            )

        db.commit()

    onboarding_weight = (
        get_onboarding_weight(
            interaction_count
        )
    )

    onboarding_categories = (
        onboarding_preferences.preferred_categories
        if onboarding_preferences
        else []
    )

    onboarding_colors = (
        onboarding_preferences.preferred_colors
        if onboarding_preferences
        else []
    )

    onboarding_styles = (
        onboarding_preferences.preferred_styles
        if onboarding_preferences
        else []
    )

    onboarding_brands = (
        onboarding_preferences.preferred_brands
        if onboarding_preferences
        else []
    )

    onboarding_occasions = (
        onboarding_preferences.occasions
        if onboarding_preferences
        else []
    )

    return {

        "category_scores":
            combine_current_preferences(
                onboarding_categories,
                learned_data[
                    "category_weights"
                ],
                onboarding_weight,
            ),

        "color_scores":
            combine_current_preferences(
                onboarding_colors,
                learned_data[
                    "color_weights"
                ],
                onboarding_weight,
            ),

        "style_scores":
            combine_current_preferences(
                onboarding_styles,
                learned_data[
                    "style_weights"
                ],
                onboarding_weight,
            ),

        "brand_scores":
            combine_current_preferences(
                onboarding_brands,
                learned_data[
                    "brand_weights"
                ],
                onboarding_weight,
            ),

        "occasion_scores":
            combine_current_preferences(
                onboarding_occasions,
                learned_data[
                    "occasion_weights"
                ],
                onboarding_weight,
            ),
    }


# ============================================================
# ENRICHED CURRENT PROFILE
# ============================================================

@router.get(
    "/profile/enriched-current-preferences",
    response_model=EnrichedCurrentPreferencesResponse,
)
def get_enriched_current_preferences(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Builds the final enriched preference profile.

    Current Preferences:
        onboarding + dynamic learned behavior

    Logistic Regression expansion:
        Category
        Color
        Style

    Brand and Occasion:
        dynamic behavior only
    """

    # ========================================================
    # 1. GET CURRENT DYNAMIC PROFILE
    # ========================================================

    current_preferences = (
        get_current_preferences(
            current_user=current_user,
            db=db,
        )
    )

    current_categories = list(
        current_preferences[
            "category_scores"
        ].keys()
    )

    current_colors = list(
        current_preferences[
            "color_scores"
        ].keys()
    )

    current_styles = list(
        current_preferences[
            "style_scores"
        ].keys()
    )

    current_brands = list(
        current_preferences[
            "brand_scores"
        ].keys()
    )

    current_occasions = list(
        current_preferences[
            "occasion_scores"
        ].keys()
    )


    # ========================================================
    # 2. GET CHOICE PRIORITIES
    # ========================================================

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

    if onboarding_preferences:

        choice_priorities = (
            onboarding_preferences
            .choice_priorities
            or []
        )

    else:

        choice_priorities = []


    # ========================================================
    # 3. NEGATIVE BEHAVIOR PROTECTION
    # ========================================================

    interactions = (
        db.query(
            UserInteraction
        )
        .filter(
            UserInteraction.user_id
            == current_user.user_id
        )
        .all()
    )

    excluded_categories = set()
    excluded_colors = set()
    excluded_styles = set()

    if interactions:

        item_ids = [
            interaction.item_id
            for interaction
            in interactions
        ]

        products = (
            db.query(Product)
            .filter(
                Product.item_id.in_(
                    item_ids
                )
            )
            .all()
        )

        products_by_id = {
            product.item_id:
                product

            for product
            in products
        }

        category_behavior = defaultdict(
            float
        )

        color_behavior = defaultdict(
            float
        )

        style_behavior = defaultdict(
            float
        )

        for interaction in interactions:

            product = (
                products_by_id.get(
                    interaction.item_id
                )
            )

            if product is None:
                continue

            interaction_value = float(
                interaction.interaction_value
            )

            if product.category:

                category_behavior[
                    product.category
                ] += interaction_value

            for color in (
                product.color or []
            ):

                color_behavior[
                    color
                ] += interaction_value

            for style in (
                product.style or []
            ):

                style_behavior[
                    style
                ] += interaction_value

        excluded_categories = {
            category
            for category, score
            in category_behavior.items()
            if score < 0
        }

        excluded_colors = {
            color
            for color, score
            in color_behavior.items()
            if score < 0
        }

        excluded_styles = {
            style
            for style, score
            in style_behavior.items()
            if score < 0
        }

        if "Comfort" in excluded_styles:

            excluded_styles.add(
                "Comfort wear"
            )


    # ========================================================
    # 4. LOGISTIC REGRESSION PREFERENCE EXPANSION
    # ========================================================

    ml_result = (
        expand_onboarding_preferences(

            preferred_colors=(
                current_colors
            ),

            preferred_categories=(
                current_categories
            ),

            preferred_styles=(
                current_styles
            ),

            occasions=(
                current_occasions
            ),

            choice_priorities=(
                choice_priorities
            ),

            preferred_brands=(
                current_brands
            ),

            excluded_colors=list(
                excluded_colors
            ),

            excluded_categories=list(
                excluded_categories
            ),

            excluded_styles=list(
                excluded_styles
            ),
        )
    )


    # ========================================================
    # 5. FINAL RESPONSE
    # ========================================================

    return {

        "current_preferences":
            current_preferences,

        "ml_expansions":
            ml_result[
                "ml_expansions"
            ],

        "enriched_preferences":
            ml_result[
                "enriched_preferences"
            ],
    }

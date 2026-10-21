from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    User,
    UserInteraction,
    UserLearnedPreference,
    Product,
)

from app.auth import get_current_user

from app.learning_engine import (
    calculate_learned_preferences,
)


router = APIRouter()


# ============================================================
# UPDATE LEARNING PROFILE
# ============================================================

@router.post("/learning/update")
def update_learning_preferences(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Updates learned preferences from
    interaction weight + recency.
    """

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

    if not interactions:

        return {
            "message":
                "No interactions found for this user",

            "learned_preferences":
                None,
        }

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

    existing_learned_preferences = (
        db.query(
            UserLearnedPreference
        )
        .filter(
            UserLearnedPreference.user_id
            == current_user.user_id
        )
        .first()
    )

    if existing_learned_preferences:

        existing_learned_preferences.category_weights = (
            learned_data[
                "category_weights"
            ]
        )

        existing_learned_preferences.color_weights = (
            learned_data[
                "color_weights"
            ]
        )

        existing_learned_preferences.style_weights = (
            learned_data[
                "style_weights"
            ]
        )

        existing_learned_preferences.brand_weights = (
            learned_data[
                "brand_weights"
            ]
        )

        existing_learned_preferences.occasion_weights = (
            learned_data[
                "occasion_weights"
            ]
        )

        db.commit()

        db.refresh(
            existing_learned_preferences
        )

        return {
            "message": (
                "Learned preferences "
                "updated successfully"
            ),

            "learned_preferences":
                existing_learned_preferences,
        }

    new_learned_preferences = (
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
        new_learned_preferences
    )

    db.commit()

    db.refresh(
        new_learned_preferences
    )

    return {
        "message": (
            "Learned preferences "
            "created successfully"
        ),

        "learned_preferences":
            new_learned_preferences,
    }
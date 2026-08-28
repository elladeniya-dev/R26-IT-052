from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    User,
    UserOnboardingPreference,
    UserInteraction,
    UserMLPreference,
    Product,
)

from app.schemas import (
    PreferenceExpansionResponse,
)

from app.auth import get_current_user

from app.ml.preference_expansion_service import (
    expand_onboarding_preferences,
)

from app.fashion_embedding_service import (
    get_image_embedding,
    create_user_preference_vector,
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







# ============================================================
# FASHION EMBEDDING TEST ENDPOINTS
# ============================================================

@router.post("/ml/test-image-embedding")
def test_image_embedding():
    """
    Temporary FashionEmbedder test endpoint.
    """

    image_url = (
        "https://images.unsplash.com/"
        "photo-1483985988355-763728e1935b"
        "?auto=format&fit=crop&w=900&q=80"
    )

    embedding = get_image_embedding(
        image_url
    )

    return {
        "message":
            "Image embedding created successfully",

        "model_name":
            "McClain/fashion-embedder",

        "image_url":
            image_url,

        "embedding_dimension":
            len(embedding),

        "first_10_values":
            embedding[:10],
    }


@router.post("/ml/test-user-vector")
def test_user_preference_vector():
    """
    Temporary FashionEmbedder user-vector test.
    """

    interaction_items = [

        {
            "item_id": "P001",
            "image_url": (
                "https://images.unsplash.com/"
                "photo-1543076447-215ad9ba6923"
                "?auto=format&fit=crop&w=900&q=80"
            ),
            "interaction_weight": 2.0,
        },

        {
            "item_id": "P002",
            "image_url": (
                "https://images.unsplash.com/"
                "photo-1483985988355-763728e1935b"
                "?auto=format&fit=crop&w=900&q=80"
            ),
            "interaction_weight": 3.0,
        },

        {
            "item_id": "P003",
            "image_url": (
                "https://images.unsplash.com/"
                "photo-1594223274512-ad4803739b7c"
                "?auto=format&fit=crop&w=900&q=80"
            ),
            "interaction_weight": 4.0,
        },
    ]

    user_vector = (
        create_user_preference_vector(
            interaction_items
        )
    )

    return {
        "message": (
            "User preference vector "
            "created successfully"
        ),

        "model_name":
            "McClain/fashion-embedder",

        "embedding_dimension":
            len(user_vector),

        "first_10_values":
            user_vector[:10],

        "used_items":
            interaction_items,
    }


@router.post(
    "/ml/update-current-user-vector"
)
def update_current_user_vector(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Creates and saves an embedding-based
    user preference vector.
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

            "user_id":
                current_user.user_id,

            "user_preference_vector":
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

    interaction_items = []

    for interaction in interactions:

        product = (
            products_by_id.get(
                interaction.item_id
            )
        )

        if product is None:
            continue

        if not product.image_url:
            continue

        interaction_items.append({

            "item_id":
                interaction.item_id,

            "image_url":
                product.image_url,

            "interaction_type":
                interaction.interaction_type,

            "interaction_weight":
                interaction.interaction_value,
        })

    if not interaction_items:

        return {
            "message": (
                "No valid product image URLs "
                "found for this user's interactions"
            ),

            "user_id":
                current_user.user_id,

            "user_preference_vector":
                None,
        }

    user_vector = (
        create_user_preference_vector(
            interaction_items
        )
    )

    if not user_vector:

        return {
            "message":
                "Could not create user preference vector",

            "user_id":
                current_user.user_id,

            "user_preference_vector":
                None,
        }

    existing_ml_preferences = (
        db.query(
            UserMLPreference
        )
        .filter(
            UserMLPreference.user_id
            == current_user.user_id
        )
        .first()
    )

    if existing_ml_preferences:

        existing_ml_preferences.model_name = (
            "McClain/fashion-embedder"
        )

        existing_ml_preferences.embedding_dimension = (
            len(user_vector)
        )

        existing_ml_preferences.user_preference_vector = (
            user_vector
        )

        existing_ml_preferences.used_interaction_count = (
            len(interaction_items)
        )

        db.commit()

        db.refresh(
            existing_ml_preferences
        )

        saved_ml_preferences = (
            existing_ml_preferences
        )

        message = (
            "Current user ML preference vector "
            "updated and saved successfully"
        )

    else:

        new_ml_preferences = (
            UserMLPreference(

                user_id=(
                    current_user.user_id
                ),

                model_name=(
                    "McClain/fashion-embedder"
                ),

                embedding_dimension=(
                    len(user_vector)
                ),

                user_preference_vector=(
                    user_vector
                ),

                used_interaction_count=(
                    len(interaction_items)
                ),
            )
        )

        db.add(
            new_ml_preferences
        )

        db.commit()

        db.refresh(
            new_ml_preferences
        )

        saved_ml_preferences = (
            new_ml_preferences
        )

        message = (
            "Current user ML preference vector "
            "created and saved successfully"
        )

    return {
        "message":
            message,

        "user_id":
            current_user.user_id,

        "model_name":
            saved_ml_preferences.model_name,

        "embedding_dimension":
            saved_ml_preferences
            .embedding_dimension,

        "first_10_values":
            saved_ml_preferences
            .user_preference_vector[:10],

        "used_interaction_count":
            saved_ml_preferences
            .used_interaction_count,

        "used_items":
            interaction_items,
    }


@router.get(
    "/ml/current-user-vector-summary"
)
def get_current_user_vector_summary(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Returns summary of saved
    FashionEmbedder user vector.
    """

    ml_preferences = (
        db.query(
            UserMLPreference
        )
        .filter(
            UserMLPreference.user_id
            == current_user.user_id
        )
        .first()
    )

    if not ml_preferences:

        return {
            "message": (
                "No saved ML preference vector "
                "found for this user"
            ),

            "user_id":
                current_user.user_id,

            "ml_preferences":
                None,
        }

    return {
        "message":
            "Saved ML preference vector found",

        "user_id":
            current_user.user_id,

        "model_name":
            ml_preferences.model_name,

        "embedding_dimension":
            ml_preferences.embedding_dimension,

        "used_interaction_count":
            ml_preferences.used_interaction_count,

        "first_10_values":
            ml_preferences
            .user_preference_vector[:10],

        "updated_at":
            ml_preferences.updated_at,
    }




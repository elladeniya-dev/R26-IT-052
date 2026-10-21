from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    User,
    UserInteraction,
    Product,
)

from app.schemas import (
    InteractionRequest,
    InteractionResponse,
    InteractionHistoryResponse,
)

from app.auth import get_current_user


router = APIRouter()


# ============================================================
# INTERACTION VALUE
# ============================================================

def get_interaction_value(
    interaction_type: str,
) -> float:

    interaction_weights = {
        "view": 1.0,
        "click": 2.0,
        "save": 3.0,
        "select": 4.0,
        "dislike": -2.0,
    }

    return interaction_weights.get(
        interaction_type.lower(),
        1.0,
    )


# ============================================================
# SAVE USER INTERACTION
# ============================================================

@router.post(
    "/interactions",
    response_model=InteractionResponse,
)
def save_user_interaction(
    request: InteractionRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    interaction_value = (
        request.interaction_value
    )

    if interaction_value is None:

        interaction_value = (
            get_interaction_value(
                request.interaction_type
            )
        )

    new_interaction = UserInteraction(
        user_id=current_user.user_id,
        item_id=request.item_id,
        interaction_type=(
            request.interaction_type.lower()
        ),
        interaction_value=interaction_value,
    )

    db.add(new_interaction)
    db.commit()
    db.refresh(new_interaction)

    return new_interaction


# ============================================================
# INTERACTION HISTORY
# ============================================================

@router.get(
    "/interactions/history",
    response_model=InteractionHistoryResponse,
)
def get_user_interaction_history(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    interactions = (
        db.query(
            UserInteraction
        )
        .filter(
            UserInteraction.user_id
            == current_user.user_id
        )
        .order_by(
            UserInteraction.created_at.desc()
        )
        .all()
    )

    total_interactions = len(
        interactions
    )

    view_count = 0
    click_count = 0
    save_count = 0
    select_count = 0
    dislike_count = 0

    item_ids = []

    for interaction in interactions:

        interaction_type = (
            interaction
            .interaction_type
            .lower()
        )

        if interaction_type == "view":
            view_count += 1

        elif interaction_type == "click":
            click_count += 1

        elif interaction_type == "save":
            save_count += 1

        elif interaction_type == "select":
            select_count += 1

        elif interaction_type == "dislike":
            dislike_count += 1

        item_ids.append(
            interaction.item_id
        )

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

    history_items = []

    for interaction in interactions:

        product = (
            products_by_id.get(
                interaction.item_id
            )
        )

        history_items.append({

            "interaction_id":
                interaction.interaction_id,

            "item_id":
                interaction.item_id,

            "interaction_type":
                interaction.interaction_type,

            "interaction_value":
                interaction.interaction_value,

            "created_at":
                interaction.created_at,

            "product_name":
                (
                    product.product_name
                    if product
                    else None
                ),

            "category":
                (
                    product.category
                    if product
                    else None
                ),

            "color":
                (
                    product.color
                    if product
                    else None
                ),

            "style":
                (
                    product.style
                    if product
                    else None
                ),

            "brand":
                (
                    product.brand
                    if product
                    else None
                ),

            "image_url":
                (
                    product.image_url
                    if product
                    else None
                ),

            "product_url":
                (
                    product.product_url
                    if product
                    else None
                ),
        })

    return {

        "stats": {

            "total_interactions":
                total_interactions,

            "view_count":
                view_count,

            "click_count":
                click_count,

            "save_count":
                save_count,

            "select_count":
                select_count,

            "dislike_count":
                dislike_count,
        },

        "interactions":
            history_items,
    }
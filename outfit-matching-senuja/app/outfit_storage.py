from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models import OutfitSuggestion, OutfitItem


def create_unique_batch_id(user_id: str, selected_item_id: str) -> str:
    """
    Creates one batch ID for one outfit generation request.
    All outfits generated in the same request will share this batch ID.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"BATCH_{user_id}_{selected_item_id}_{timestamp}"


def create_unique_outfit_id(user_id: str, batch_id: str, index: int) -> str:
    """
    Creates a unique outfit ID.
    Example:
    OUT_USR001_BATCH_USR001_P001_20260430103045_001
    """
    return f"OUT_{user_id}_{batch_id}_{index:03d}"


def delete_existing_outfits_for_selected_item(
    db: Session,
    user_id: str,
    selected_item_id: str
):
    """
    Deletes old saved outfits for the same user and selected item.

    This prevents duplicate saved outfits when the user generates outfits
    multiple times for the same selected product.
    """

    existing_outfits = db.query(OutfitSuggestion).filter(
        OutfitSuggestion.user_id == user_id,
        OutfitSuggestion.selected_item_id == selected_item_id
    ).all()

    for outfit in existing_outfits:
        db.delete(outfit)

    db.flush()


def save_generated_outfits(
    db: Session,
    user_id: str,
    selected_item_id: str,
    outfits: List[Dict]
) -> List[Dict]:
    """
    Saves generated outfit suggestions into:
    1. outfit_suggestions table
    2. outfit_items table

    Improvement:
    - Deletes old outfits for same user + selected item
    - Creates one generation_batch_id for the new request
    - Saves the new outfits under that batch
    """

    saved_outfits = []

    try:
        delete_existing_outfits_for_selected_item(
            db=db,
            user_id=user_id,
            selected_item_id=selected_item_id
        )

        batch_id = create_unique_batch_id(
            user_id=user_id,
            selected_item_id=selected_item_id
        )

        for index, outfit in enumerate(outfits, start=1):
            new_outfit_id = create_unique_outfit_id(
                user_id=user_id,
                batch_id=batch_id,
                index=index
            )

            outfit_suggestion = OutfitSuggestion(
                outfit_id=new_outfit_id,
                generation_batch_id=batch_id,
                user_id=user_id,
                selected_item_id=selected_item_id,
                compatibility_score=outfit["compatibility_score"],
                reason_tags=outfit["reason_tags"]
            )

            db.add(outfit_suggestion)

            for item in outfit["items"]:
                outfit_item = OutfitItem(
                    outfit_id=new_outfit_id,
                    item_id=item["item_id"],
                    role=item["role"]
                )

                db.add(outfit_item)

            copied_outfit = outfit.copy()
            copied_outfit["outfit_id"] = new_outfit_id
            copied_outfit["generation_batch_id"] = batch_id
            saved_outfits.append(copied_outfit)

        db.commit()
        return saved_outfits

    except Exception as e:
        db.rollback()
        raise e


<<<<<<< HEAD
def product_to_full_response(product: Product, role: str) -> Dict:
    """
    Converts a Product database row into a full API response object.
    """

    if not product:
        return {
            "item_id": None,
            "role": role,
            "message": "Product details not found"
        }

    return {
        "item_id": product.item_id,
        "title": product.title,
        "role": role,
        "category": product.category,
        "subcategory": product.subcategory,
        "color": product.color,
        "style": product.style,
        "brand": product.brand,
        "price": product.price,
        "currency": product.currency,
        "image_url": product.image_url,
        "product_url": product.product_url,
        "availability": product.availability
    }


def outfit_record_to_response(db: Session, outfit: OutfitSuggestion) -> Dict:
    """
    Converts one saved OutfitSuggestion record into API response format.
    Includes full product details for each outfit item.
    """

    full_items = []

    for outfit_item in outfit.items:
        product = db.query(Product).filter(
            Product.item_id == outfit_item.item_id
        ).first()

        full_items.append(
            product_to_full_response(
                product=product,
                role=outfit_item.role
            )
        )

    return {
        "outfit_id": outfit.outfit_id,
        "generation_batch_id": outfit.generation_batch_id,
        "user_id": outfit.user_id,
        "selected_item_id": outfit.selected_item_id,
        "compatibility_score": outfit.compatibility_score,
        "reason_tags": outfit.reason_tags,
        "generated_at": outfit.generated_at.isoformat() if outfit.generated_at else None,
        "items": full_items
    }


def get_saved_outfits_by_user(db: Session, user_id: str) -> List[Dict]:
    """
    Reads all saved outfits for one user.
=======
def get_saved_outfits_by_user(db: Session, user_id: str) -> List[Dict]:
    """
    Reads previously saved outfits for one user.
>>>>>>> parent of 84fbb9d (Enhance outfit retrieval to include full product details and improve response format)
    """

    outfit_records = db.query(OutfitSuggestion).filter(
        OutfitSuggestion.user_id == user_id
    ).order_by(
        OutfitSuggestion.generated_at.desc()
    ).all()

    return [
        outfit_record_to_response(db=db, outfit=outfit)
        for outfit in outfit_records
    ]

<<<<<<< HEAD

def get_latest_outfit_batch_by_user(db: Session, user_id: str) -> Dict:
    """
    Reads only the latest outfit generation batch for one user.

    Example:
    If user generated outfits for P001 at 10:00
    and then generated outfits for P007 at 10:10,
    this returns only the P007 batch.
    """

    latest_outfit = db.query(OutfitSuggestion).filter(
        OutfitSuggestion.user_id == user_id
    ).order_by(
        OutfitSuggestion.generated_at.desc()
    ).first()
=======
    for outfit in outfit_records:
        saved_outfits.append({
            "outfit_id": outfit.outfit_id,
            "user_id": outfit.user_id,
            "selected_item_id": outfit.selected_item_id,
            "compatibility_score": outfit.compatibility_score,
            "reason_tags": outfit.reason_tags,
            "generated_at": outfit.generated_at.isoformat() if outfit.generated_at else None,
            "items": [
                {
                    "item_id": item.item_id,
                    "role": item.role
                }
                for item in outfit.items
            ]
        })
>>>>>>> parent of 84fbb9d (Enhance outfit retrieval to include full product details and improve response format)

    if not latest_outfit:
        return {
            "generation_batch_id": None,
            "selected_item_id": None,
            "outfits": []
        }

    latest_batch_id = latest_outfit.generation_batch_id

    latest_batch_outfits = db.query(OutfitSuggestion).filter(
        OutfitSuggestion.user_id == user_id,
        OutfitSuggestion.generation_batch_id == latest_batch_id
    ).order_by(
        OutfitSuggestion.compatibility_score.desc()
    ).all()

    return {
        "generation_batch_id": latest_batch_id,
        "selected_item_id": latest_outfit.selected_item_id,
        "outfits": [
            outfit_record_to_response(db=db, outfit=outfit)
            for outfit in latest_batch_outfits
        ]
    }
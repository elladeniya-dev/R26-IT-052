from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models import OutfitSuggestion, OutfitItem, Product


def create_unique_outfit_id(user_id: str, index: int) -> str:
    """
    Creates a simple unique outfit ID using user_id, timestamp, and index.
    Example:
    OUT_USR001_20260430103045_001
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"OUT_{user_id}_{timestamp}_{index:03d}"


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

    Returns the same outfits with database-safe outfit IDs.
    """

    saved_outfits = []

    try:
        for index, outfit in enumerate(outfits, start=1):
            new_outfit_id = create_unique_outfit_id(user_id=user_id, index=index)

            outfit_suggestion = OutfitSuggestion(
                outfit_id=new_outfit_id,
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
            saved_outfits.append(copied_outfit)

        db.commit()
        return saved_outfits

    except Exception as e:
        db.rollback()
        raise e


def product_to_response(product: Product, role: str) -> Dict:
    """
    Converts saved product data into mobile-app-friendly response format.
    """

    if not product:
        return {
            "item_id": None,
            "role": role,
            "title": "Product not found",
            "category": role,
            "subcategory": None,
            "color": [],
            "style": [],
            "brand": None,
            "price": None,
            "currency": None,
            "image_url": None,
            "product_url": None
        }

    return {
        "item_id": product.item_id,
        "role": role,
        "title": product.title,
        "category": product.category,
        "subcategory": product.subcategory,
        "color": product.color,
        "style": product.style,
        "brand": product.brand,
        "price": product.price,
        "currency": product.currency,
        "image_url": product.image_url,
        "product_url": product.product_url
    }


def get_saved_outfits_by_user(db: Session, user_id: str) -> List[Dict]:
    """
    Reads previously saved outfits for one user.
    Now returns full product details for each outfit item.
    """

    outfit_records = db.query(OutfitSuggestion).filter(
        OutfitSuggestion.user_id == user_id
    ).order_by(
        OutfitSuggestion.generated_at.desc()
    ).all()

    saved_outfits = []

    for outfit in outfit_records:
        full_items = []

        for saved_item in outfit.items:
            product = db.query(Product).filter(
                Product.item_id == saved_item.item_id
            ).first()

            full_items.append(
                product_to_response(
                    product=product,
                    role=saved_item.role
                )
            )

        saved_outfits.append({
            "outfit_id": outfit.outfit_id,
            "user_id": outfit.user_id,
            "selected_item_id": outfit.selected_item_id,
            "compatibility_score": outfit.compatibility_score,
            "reason_tags": outfit.reason_tags,
            "generated_at": outfit.generated_at.isoformat() if outfit.generated_at else None,
            "items": full_items
        })

    return saved_outfits
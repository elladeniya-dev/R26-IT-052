from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models import OutfitSuggestion, OutfitItem


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


def get_saved_outfits_by_user(db: Session, user_id: str) -> List[Dict]:
    """
    Reads previously saved outfits for one user.
    """

    outfit_records = db.query(OutfitSuggestion).filter(
        OutfitSuggestion.user_id == user_id
    ).order_by(
        OutfitSuggestion.generated_at.desc()
    ).all()

    saved_outfits = []

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

    return saved_outfits
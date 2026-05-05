from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import OutfitGenerateRequest
from app.outfit_generator import generate_outfits_for_selected_item
from app.outfit_storage import (
    save_generated_outfits,
    get_saved_outfits_by_user,
    get_latest_outfit_batch_by_user
)


router = APIRouter(
    prefix="/outfits",
    tags=["Outfits"]
)


@router.post("/generate")
def generate_outfits(
    request: OutfitGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate compatible outfit suggestions for a selected item.

    This endpoint:
    1. Receives selected item ID from the mobile app
    2. Applies optional filters
    3. Generates compatible outfits
    4. Scores and ranks outfits
    5. Saves the latest generated outfits
    """

    try:
        result = generate_outfits_for_selected_item(
            db=db,
            user_id=request.user_id,
            selected_item_id=request.selected_item_id,
            occasion=request.occasion,
            max_outfits=request.max_outfits,
            min_price=request.min_price,
            max_price=request.max_price,
            preferred_colors=request.preferred_colors,
            excluded_categories=request.excluded_categories,
            max_items_per_category=request.max_items_per_category
        )

        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=result["message"]
            )

        saved_outfits = save_generated_outfits(
            db=db,
            user_id=result["user_id"],
            selected_item_id=result["selected_item_id"],
            outfits=result["outfits"]
        )

        return {
            "status": "success",
            "message": "Outfits generated successfully. Previous saved outfits for the same selected item were replaced.",
            "user_id": result["user_id"],
            "selected_item_id": result["selected_item_id"],
            "outfits": saved_outfits,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate outfits: {str(e)}"
        )


@router.get("/latest/{user_id}")
def get_latest_user_outfits(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get only the latest generated outfit batch for a user.

    Endpoint:
    GET /outfits/latest/{user_id}

    Example:
    GET /outfits/latest/USR001
    """

    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=400,
                detail="user_id cannot be empty"
            )

        cleaned_user_id = user_id.strip()

        latest_batch = get_latest_outfit_batch_by_user(
            db=db,
            user_id=cleaned_user_id
        )

        return {
            "status": "success",
            "user_id": cleaned_user_id,
            "generation_batch_id": latest_batch["generation_batch_id"],
            "selected_item_id": latest_batch["selected_item_id"],
            "total_outfits": len(latest_batch["outfits"]),
            "outfits": latest_batch["outfits"]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve latest outfit batch: {str(e)}"
        )


@router.get("/{user_id}")
def get_user_outfits(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all saved outfit suggestions for a user.

    Endpoint:
    GET /outfits/{user_id}

    Example:
    GET /outfits/USR001
    """

    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=400,
                detail="user_id cannot be empty"
            )

        cleaned_user_id = user_id.strip()

        saved_outfits = get_saved_outfits_by_user(
            db=db,
            user_id=cleaned_user_id
        )

        return {
            "status": "success",
            "user_id": cleaned_user_id,
            "total_outfits": len(saved_outfits),
            "outfits": saved_outfits
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve outfits: {str(e)}"
        )
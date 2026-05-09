from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OutfitSuggestion
from app.outfit_storage import outfit_record_to_response


router = APIRouter(
    prefix="/saved-outfits",
    tags=["Saved Outfits"]
)


@router.post("/save/{outfit_id}")
def save_outfit(
    outfit_id: str,
    db: Session = Depends(get_db)
):
    """
    Mark a generated outfit as saved.

    The outfit must already exist in outfit_suggestions.
    """

    try:
        if not outfit_id or not outfit_id.strip():
            raise HTTPException(
                status_code=400,
                detail="outfit_id cannot be empty"
            )

        cleaned_outfit_id = outfit_id.strip()

        outfit = db.query(OutfitSuggestion).filter(
            OutfitSuggestion.outfit_id == cleaned_outfit_id
        ).first()

        if not outfit:
            raise HTTPException(
                status_code=404,
                detail="Outfit not found"
            )

        outfit.is_saved = True
        db.commit()
        db.refresh(outfit)

        return {
            "status": "success",
            "message": "Outfit saved successfully",
            "outfit": outfit_record_to_response(db=db, outfit=outfit)
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save outfit: {str(e)}"
        )


@router.get("/{user_id}")
def get_saved_outfits(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all saved outfits for a user.
    """

    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=400,
                detail="user_id cannot be empty"
            )

        cleaned_user_id = user_id.strip()

        saved_outfits = db.query(OutfitSuggestion).filter(
            OutfitSuggestion.user_id == cleaned_user_id,
            OutfitSuggestion.is_saved == True
        ).order_by(
            OutfitSuggestion.generated_at.desc()
        ).all()

        return {
            "status": "success",
            "user_id": cleaned_user_id,
            "total_saved_outfits": len(saved_outfits),
            "saved_outfits": [
                outfit_record_to_response(db=db, outfit=outfit)
                for outfit in saved_outfits
            ]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve saved outfits: {str(e)}"
        )


@router.get("/detail/{outfit_id}")
def get_saved_outfit_detail(
    outfit_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details of one saved outfit.
    """

    try:
        if not outfit_id or not outfit_id.strip():
            raise HTTPException(
                status_code=400,
                detail="outfit_id cannot be empty"
            )

        cleaned_outfit_id = outfit_id.strip()

        outfit = db.query(OutfitSuggestion).filter(
            OutfitSuggestion.outfit_id == cleaned_outfit_id,
            OutfitSuggestion.is_saved == True
        ).first()

        if not outfit:
            raise HTTPException(
                status_code=404,
                detail="Saved outfit not found"
            )

        return {
            "status": "success",
            "saved_outfit": outfit_record_to_response(db=db, outfit=outfit)
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve saved outfit detail: {str(e)}"
        )


@router.delete("/{outfit_id}")
def remove_saved_outfit(
    outfit_id: str,
    db: Session = Depends(get_db)
):
    """
    Remove an outfit from saved list.

    This does not delete the generated outfit from database.
    It only changes is_saved from true to false.
    """

    try:
        if not outfit_id or not outfit_id.strip():
            raise HTTPException(
                status_code=400,
                detail="outfit_id cannot be empty"
            )

        cleaned_outfit_id = outfit_id.strip()

        outfit = db.query(OutfitSuggestion).filter(
            OutfitSuggestion.outfit_id == cleaned_outfit_id
        ).first()

        if not outfit:
            raise HTTPException(
                status_code=404,
                detail="Outfit not found"
            )

        if not outfit.is_saved:
            return {
                "status": "success",
                "message": "Outfit was already removed from saved list",
                "outfit_id": cleaned_outfit_id
            }

        outfit.is_saved = False
        db.commit()

        return {
            "status": "success",
            "message": "Outfit removed from saved list successfully",
            "outfit_id": cleaned_outfit_id
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove saved outfit: {str(e)}"
        )
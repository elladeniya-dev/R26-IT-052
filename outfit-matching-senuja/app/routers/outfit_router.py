from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import OutfitGenerateRequest
from app.outfit_generator import generate_outfits_for_selected_item
from app.outfit_storage import save_generated_outfits, get_latest_outfit_batch_by_user


router = APIRouter(
    prefix="/outfits",
    tags=["Outfits"]
)


@router.post("/generate")
def generate_outfits(
    request: OutfitGenerateRequest,
    db: Session = Depends(get_db)
):
    try:
        result = generate_outfits_for_selected_item(
            db=db,
            user_id=request.user_id,
            selected_item_id=request.selected_item_id,
            occasion=request.occasion,
            max_outfits=request.max_outfits
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
            "user_id": result["user_id"],
            "selected_item_id": result["selected_item_id"],
            "outfits": saved_outfits,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while generating outfits: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while generating outfits: {str(e)}"
        )


@router.get("/{user_id}")
def get_user_outfits(
    user_id: str,
    db: Session = Depends(get_db)
):
    try:
        latest_batch = get_latest_outfit_batch_by_user(
            db=db,
            user_id=user_id
        )
        return {
            "user_id": user_id,
            "generation_batch_id": latest_batch["generation_batch_id"],
            "selected_item_id": latest_batch["selected_item_id"],
            "outfits": latest_batch["outfits"]
        }
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while reading saved outfits: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while reading saved outfits: {str(e)}"
        )
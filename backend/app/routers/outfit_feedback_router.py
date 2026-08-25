from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.s_database import get_db
from app.s_schemas import OutfitFeedbackRequest
from app.s_outfit_feedback import (
    get_feedback_by_user,
    get_feedback_report_by_user,
    get_feedback_summary_by_user,
    save_outfit_feedback,
)


router = APIRouter(
    prefix="/outfits",
    tags=["Outfit Feedback"]
)


@router.post("/{outfit_id}/feedback")
def submit_outfit_feedback(
    outfit_id: str,
    request: OutfitFeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Save a user rating for a generated outfit.
    Ratings support research evaluation of outfit compatibility quality.
    """

    try:
        if not outfit_id or not outfit_id.strip():
            raise HTTPException(
                status_code=400,
                detail="outfit_id cannot be empty"
            )

        result = save_outfit_feedback(
            db=db,
            outfit_id=outfit_id.strip(),
            user_id=request.user_id,
            rating=request.rating,
            comment=request.comment
        )

        if not result["success"]:
            status_code = 404

            if result["message"] == "Feedback user does not match outfit user":
                status_code = 403

            raise HTTPException(
                status_code=status_code,
                detail=result["message"]
            )

        return {
            "status": "success",
            "message": result["message"],
            "feedback": result["feedback"]
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save outfit feedback: {str(e)}"
        )


@router.get("/feedback/{user_id}")
def get_user_feedback(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all outfit feedback records for one user.
    """

    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=400,
                detail="user_id cannot be empty"
            )

        cleaned_user_id = user_id.strip()
        feedback_records = get_feedback_by_user(
            db=db,
            user_id=cleaned_user_id
        )

        return {
            "status": "success",
            "user_id": cleaned_user_id,
            "total_feedback": len(feedback_records),
            "feedback": feedback_records
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve outfit feedback: {str(e)}"
        )


@router.get("/feedback-summary/{user_id}")
def get_user_feedback_summary(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get rating summary values for research evaluation.
    """

    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=400,
                detail="user_id cannot be empty"
            )

        summary = get_feedback_summary_by_user(
            db=db,
            user_id=user_id.strip()
        )

        return {
            "status": "success",
            "summary": summary
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve feedback summary: {str(e)}"
        )


@router.get("/feedback-report/{user_id}")
def get_user_feedback_report(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get report-ready feedback data for research evaluation.
    """

    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=400,
                detail="user_id cannot be empty"
            )

        report = get_feedback_report_by_user(
            db=db,
            user_id=user_id.strip()
        )

        return {
            "status": "success",
            "report": report
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve feedback report: {str(e)}"
        )

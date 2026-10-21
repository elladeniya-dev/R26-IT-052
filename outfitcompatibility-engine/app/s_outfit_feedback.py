from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.s_models import OutfitFeedback, OutfitSuggestion


def create_unique_feedback_id(user_id: str, outfit_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"FDB_{user_id}_{outfit_id}_{timestamp}"


def feedback_record_to_response(feedback: OutfitFeedback) -> Dict:
    return {
        "feedback_id": feedback.feedback_id,
        "user_id": feedback.user_id,
        "outfit_id": feedback.outfit_id,
        "selected_item_id": feedback.selected_item_id,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "created_at": feedback.created_at.isoformat()
        if feedback.created_at else None,
    }


def save_outfit_feedback(
    db: Session,
    outfit_id: str,
    user_id: str,
    rating: int,
    comment: Optional[str] = None
) -> Dict:
    outfit = db.query(OutfitSuggestion).filter(
        OutfitSuggestion.outfit_id == outfit_id
    ).first()

    if not outfit:
        return {
            "success": False,
            "message": "Outfit not found",
            "feedback": None
        }

    if outfit.user_id != user_id:
        return {
            "success": False,
            "message": "Feedback user does not match outfit user",
            "feedback": None
        }

    feedback = OutfitFeedback(
        feedback_id=create_unique_feedback_id(
            user_id=user_id,
            outfit_id=outfit_id
        ),
        user_id=user_id,
        outfit_id=outfit_id,
        selected_item_id=outfit.selected_item_id,
        rating=rating,
        comment=comment
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "success": True,
        "message": "Outfit feedback saved successfully",
        "feedback": feedback_record_to_response(feedback)
    }


def get_feedback_by_user(db: Session, user_id: str) -> List[Dict]:
    feedback_records = db.query(OutfitFeedback).filter(
        OutfitFeedback.user_id == user_id
    ).order_by(
        OutfitFeedback.created_at.desc()
    ).all()

    return [
        feedback_record_to_response(feedback)
        for feedback in feedback_records
    ]


def get_feedback_summary_by_user(db: Session, user_id: str) -> Dict:
    feedback_records = db.query(OutfitFeedback).filter(
        OutfitFeedback.user_id == user_id
    ).all()

    total_feedback = len(feedback_records)

    if total_feedback == 0:
        return {
            "user_id": user_id,
            "total_feedback": 0,
            "average_rating": 0.0,
            "good_matches": 0,
            "okay_matches": 0,
            "bad_matches": 0,
            "rating_distribution": {
                "1": 0,
                "2": 0,
                "3": 0,
                "4": 0,
                "5": 0
            }
        }

    rating_distribution = {
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0
    }

    for feedback in feedback_records:
        rating_distribution[str(feedback.rating)] += 1

    good_matches = sum(
        1 for feedback in feedback_records
        if feedback.rating >= 4
    )
    okay_matches = sum(
        1 for feedback in feedback_records
        if feedback.rating == 3
    )
    bad_matches = sum(
        1 for feedback in feedback_records
        if feedback.rating <= 2
    )
    average_rating = sum(
        feedback.rating for feedback in feedback_records
    ) / total_feedback

    return {
        "user_id": user_id,
        "total_feedback": total_feedback,
        "average_rating": round(average_rating, 2),
        "good_matches": good_matches,
        "okay_matches": okay_matches,
        "bad_matches": bad_matches,
        "rating_distribution": rating_distribution
    }


def get_feedback_report_by_user(db: Session, user_id: str) -> Dict:
    feedback_records = get_feedback_by_user(
        db=db,
        user_id=user_id
    )
    summary = get_feedback_summary_by_user(
        db=db,
        user_id=user_id
    )

    total_feedback = summary["total_feedback"]
    good_match_ratio = 0.0

    if total_feedback > 0:
        good_match_ratio = summary["good_matches"] / total_feedback

    return {
        "user_id": user_id,
        "summary": summary,
        "feedback_records": feedback_records,
        "research_notes": {
            "evaluation_method": "User feedback rating from 1 to 5 collected after outfit generation",
            "rating_scale": {
                "1": "Bad match",
                "2": "Weak match",
                "3": "Okay match",
                "4": "Good match",
                "5": "Excellent match"
            },
            "success_measure": "Average rating and good match ratio",
            "good_match_ratio": round(good_match_ratio, 2),
            "component": "Outfit Matching and Clothing Style Compatibility Engine"
        }
    }

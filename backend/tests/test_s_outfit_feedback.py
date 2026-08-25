from pathlib import Path
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.s_database import Base
from app.s_models import OutfitSuggestion
from app.s_outfit_feedback import (
    get_feedback_report_by_user,
    get_feedback_summary_by_user,
    save_outfit_feedback,
)


def create_test_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def add_outfit(db, outfit_id="OUT001", user_id="USR001"):
    db.add(
        OutfitSuggestion(
            outfit_id=outfit_id,
            generation_batch_id="BATCH001",
            user_id=user_id,
            selected_item_id="P001",
            compatibility_score=0.92,
            reason_tags=["matching casual style"],
            is_saved=False,
        )
    )
    db.commit()


def test_save_outfit_feedback_successfully():
    db = create_test_session()

    try:
        add_outfit(db)

        result = save_outfit_feedback(
            db=db,
            outfit_id="OUT001",
            user_id="USR001",
            rating=5,
            comment="Good outfit match",
        )

        assert result["success"] is True
        assert result["feedback"]["rating"] == 5
        assert result["feedback"]["selected_item_id"] == "P001"

    finally:
        db.close()


def test_feedback_summary_counts_ratings():
    db = create_test_session()

    try:
        add_outfit(db, outfit_id="OUT001")
        add_outfit(db, outfit_id="OUT002")
        add_outfit(db, outfit_id="OUT003")

        save_outfit_feedback(db, "OUT001", "USR001", 5, "Good")
        save_outfit_feedback(db, "OUT002", "USR001", 3, "Okay")
        save_outfit_feedback(db, "OUT003", "USR001", 1, "Bad")

        summary = get_feedback_summary_by_user(
            db=db,
            user_id="USR001",
        )

        assert summary["total_feedback"] == 3
        assert summary["average_rating"] == 3.0
        assert summary["good_matches"] == 1
        assert summary["okay_matches"] == 1
        assert summary["bad_matches"] == 1
        assert summary["rating_distribution"]["5"] == 1

    finally:
        db.close()


def test_save_outfit_feedback_rejects_wrong_user():
    db = create_test_session()

    try:
        add_outfit(db, user_id="USR001")

        result = save_outfit_feedback(
            db=db,
            outfit_id="OUT001",
            user_id="USR999",
            rating=5,
            comment=None,
        )

        assert result["success"] is False
        assert result["message"] == "Feedback user does not match outfit user"

    finally:
        db.close()


def test_feedback_report_contains_research_notes_and_records():
    db = create_test_session()

    try:
        add_outfit(db, outfit_id="OUT001")
        add_outfit(db, outfit_id="OUT002")

        save_outfit_feedback(db, "OUT001", "USR001", 5, "Good")
        save_outfit_feedback(db, "OUT002", "USR001", 3, "Okay")

        report = get_feedback_report_by_user(
            db=db,
            user_id="USR001",
        )

        assert report["user_id"] == "USR001"
        assert report["summary"]["total_feedback"] == 2
        assert len(report["feedback_records"]) == 2
        assert report["research_notes"]["good_match_ratio"] == 0.5
        assert (
            report["research_notes"]["component"]
            == "Outfit Matching and Clothing Style Compatibility Engine"
        )

    finally:
        db.close()


if __name__ == "__main__":
    test_save_outfit_feedback_successfully()
    test_feedback_summary_counts_ratings()
    test_save_outfit_feedback_rejects_wrong_user()
    test_feedback_report_contains_research_notes_and_records()
    print("Outfit feedback tests passed.")

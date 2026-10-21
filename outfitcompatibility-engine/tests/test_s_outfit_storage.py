from pathlib import Path
import os
import sys
from types import ModuleType

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker


SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

test_database = ModuleType("app.database")
test_database.Base = declarative_base()
sys.modules["app.database"] = test_database

from app.s_database import Base
from app.s_models import OutfitSuggestion
from app.s_outfit_storage import (
    delete_unsaved_outfits_for_selected_item,
    outfit_record_to_response,
)


def test_delete_unsaved_outfits_keeps_saved_outfits():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        saved_outfit = OutfitSuggestion(
            outfit_id="OUT_SAVED",
            generation_batch_id="BATCH_OLD",
            user_id="USR001",
            selected_item_id="P001",
            compatibility_score=0.95,
            reason_tags=["saved"],
            is_saved=True,
        )
        unsaved_outfit = OutfitSuggestion(
            outfit_id="OUT_UNSAVED",
            generation_batch_id="BATCH_OLD",
            user_id="USR001",
            selected_item_id="P001",
            compatibility_score=0.75,
            reason_tags=["temporary"],
            is_saved=False,
        )

        db.add_all([saved_outfit, unsaved_outfit])
        db.commit()

        delete_unsaved_outfits_for_selected_item(
            db=db,
            user_id="USR001",
            selected_item_id="P001",
        )
        db.commit()

        remaining_outfits = db.query(OutfitSuggestion).all()

        assert len(remaining_outfits) == 1
        assert remaining_outfits[0].outfit_id == "OUT_SAVED"

        response = outfit_record_to_response(db=db, outfit=remaining_outfits[0])
        assert response["is_saved"] is True

    finally:
        db.close()


if __name__ == "__main__":
    test_delete_unsaved_outfits_keeps_saved_outfits()
    print("Outfit storage test passed.")

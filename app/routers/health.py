from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(tags=["Health & Status"])


@router.get("/")
def home():
    return {"message": "Gividu Trend Analysis Engine is running successfully"}


@router.get("/test-db")
def test_database_connection(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1"))
        value = result.scalar()

        return {
            "database_connected": True,
            "test_result": value,
            "message": "PostgreSQL connection successful",
        }

    except Exception as e:
        return {"database_connected": False, "error": str(e)}

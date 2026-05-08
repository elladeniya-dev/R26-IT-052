from fastapi import APIRouter
from sqlalchemy import text

from app.database import engine


router = APIRouter(
    tags=["Health Check"]
)


@router.get("/")
def home():
    return {
        "status": "success",
        "message": "Senu Outfit Compatibility Engine is running successfully"
    }


@router.get("/test-db")
def test_database_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()

        return {
            "status": "success",
            "database_connected": True,
            "test_result": value,
            "message": "PostgreSQL connection successful"
        }

    except Exception as e:
        return {
            "status": "error",
            "database_connected": False,
            "error": str(e),
            "message": "PostgreSQL connection failed"
        }
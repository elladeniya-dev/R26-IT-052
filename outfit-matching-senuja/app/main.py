from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine


app = FastAPI(
    title="Senu Outfit Compatibility Engine",
    description="Rule-based outfit compatibility backend service for Smart Fashion Assistant",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Senu Outfit Compatibility Engine is running successfully"
    }


@app.get("/test-db")
def test_database_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()

        return {
            "database_connected": True,
            "test_result": value,
            "message": "PostgreSQL connection successful"
        }

    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e),
            "message": "PostgreSQL connection failed"
        }
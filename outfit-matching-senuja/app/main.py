from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app import models


Base.metadata.create_all(bind=engine)

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


@app.get("/products")
def get_all_products():
    db: Session = next(get_db())

    try:
        products = db.query(models.Product).all()

        return {
            "total_products": len(products),
            "products": [
                {
                    "item_id": product.item_id,
                    "title": product.title,
                    "category": product.category,
                    "subcategory": product.subcategory,
                    "color": product.color,
                    "style": product.style,
                    "brand": product.brand,
                    "price": product.price,
                    "currency": product.currency,
                    "image_url": product.image_url,
                    "product_url": product.product_url,
                    "availability": product.availability
                }
                for product in products
            ]
        }

    finally:
        db.close()
from datetime import datetime, timezone

from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app import models
from app.schemas import OutfitGenerateRequest
from app.outfit_generator import generate_outfits_for_selected_item
from app.outfit_storage import save_generated_outfits, get_saved_outfits_by_user


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
def get_all_products(db: Session = Depends(get_db)):
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


@app.post("/outfits/generate")
def generate_outfits(
    request: OutfitGenerateRequest,
    db: Session = Depends(get_db)
):
    result = generate_outfits_for_selected_item(
        db=db,
        user_id=request.user_id,
        selected_item_id=request.selected_item_id,
        occasion=request.occasion,
        max_outfits=request.max_outfits
    )

    if not result["success"]:
        return {
            "user_id": request.user_id,
            "selected_item_id": request.selected_item_id,
            "outfits": [],
            "message": result["message"],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

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


@app.get("/outfits/{user_id}")
def get_user_outfits(
    user_id: str,
    db: Session = Depends(get_db)
):
    saved_outfits = get_saved_outfits_by_user(
        db=db,
        user_id=user_id
    )

    return {
        "user_id": user_id,
        "total_outfits": len(saved_outfits),
        "outfits": saved_outfits
    }
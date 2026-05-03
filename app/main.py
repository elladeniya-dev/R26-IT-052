from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import engine, Base, get_db
from app import models, schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gividu Trend Analysis Engine",
    description="Trend Analysis backend service for Smart Fashion Assistant",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Gividu Trend Analysis Engine is running successfully"
    }


@app.get("/test-db")
def test_database_connection(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1"))
        value = result.scalar()

        return {
            "database_connected": True,
            "test_result": value,
            "message": "PostgreSQL connection successful"
        }

    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e)
        }


@app.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    new_product = models.Product(
        item_id=product.item_id,
        title=product.title,
        category=product.category,
        subcategory=product.subcategory,
        color=product.color,
        style=product.style,
        brand=product.brand,
        price=product.price,
        currency=product.currency,
        image_url=product.image_url,
        product_url=product.product_url,
        source=product.source,
        description=product.description,
        availability=product.availability,
        collected_at=product.collected_at
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@app.get("/products/")
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()

    return {
        "total_products": len(products),
        "products": products
    }
from fastapi import FastAPI

from app.database import engine, Base
from app.models.product import Product
from app.routes import product_routes,  recommendation_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Koji Backend - Smart Fashion Assistant",
    description="Data Collection and Recommendation Engine backend",
    version="1.0.0"
)

app.include_router(product_routes.router)
app.include_router(recommendation_routes.router)


@app.get("/")
def home():
    return {
        "message": "Koji backend is running successfully"
    }
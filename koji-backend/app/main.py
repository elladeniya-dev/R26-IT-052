from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.models.product import Product
from app.routes import product_routes, recommendation_routes, crawler_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Koji Backend - Smart Fashion Assistant",
    description="Data Collection and Recommendation Engine backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(product_routes.router)
app.include_router(recommendation_routes.router)
app.include_router(crawler_routes.router)


@app.get("/")
def home():
    return {
        "message": "Koji backend is running successfully"
    }
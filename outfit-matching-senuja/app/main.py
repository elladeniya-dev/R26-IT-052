from fastapi import FastAPI

from app.database import engine, Base
from app import models
from app.routers import health_router, product_router, outfit_router


app = FastAPI(
    title="Senu Outfit Compatibility Engine",
    description="Rule-based outfit compatibility backend service for Smart Fashion Assistant",
    version="1.0.0"
)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


app.include_router(health_router.router)
app.include_router(product_router.router)
app.include_router(outfit_router.router)
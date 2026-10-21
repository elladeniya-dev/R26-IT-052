from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.s_database import engine, Base
from app import s_models
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    health_router,
    product_router,
    outfit_router,
    outfit_feedback_router,
    saved_outfit_router
)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs when the FastAPI application starts.
    Creates database tables if they do not already exist.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Senu Outfit Compatibility Engine",
    description="Rule-based outfit compatibility backend service for Smart Fashion Assistant",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


app.include_router(health_router.router)
app.include_router(product_router.router)
app.include_router(outfit_router.router)
app.include_router(outfit_feedback_router.router)
app.include_router(saved_outfit_router.router)

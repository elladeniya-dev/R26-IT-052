from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.routers import (
    health,
    products,
    trend_observations,
    trends,
    ml_predictions,
    insights,
    recommendations,
    trending_products,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gividu Trend Analysis Engine",
    description="Trend Analysis backend service for Smart Fashion Assistant",
    version="1.0.0",
)

# Open by default (read-only trend data, no auth/user data on this API) —
# tighten to specific origins once the client app's real domain is known.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(products.router)
app.include_router(trend_observations.router)
app.include_router(trends.router)
app.include_router(ml_predictions.router)
app.include_router(insights.router)
app.include_router(recommendations.router)
app.include_router(trending_products.router)
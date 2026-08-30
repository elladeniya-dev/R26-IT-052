from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base

from app.routes.auth_routes import router as auth_router
from app.routes.onboarding_routes import router as onboarding_router
from app.routes.profile_routes import router as profile_router
from app.routes.interaction_routes import router as interaction_router
from app.routes.product_routes import router as product_router
from app.routes.learning_routes import router as learning_router
from app.routes.ml_routes import router as ml_router

from app.routes.integration_routes import router as integration_router

# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Smart Fashion Assistant - Chala Backend",
    description=(
        "Backend for Google Sign-In, Onboarding, "
        "User Profile, and User Learning Engine"
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "https://r26-it-052.onrender.com",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(profile_router)
app.include_router(interaction_router)
app.include_router(product_router)
app.include_router(learning_router)
app.include_router(ml_router)
app.include_router(integration_router)

# ============================================================
# BASIC ENDPOINTS
# ============================================================

@app.get("/")
def home():
    return {
        "message": "Chala backend is running successfully"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": "connected",
        "module": "user-profiling-chalani",
    }

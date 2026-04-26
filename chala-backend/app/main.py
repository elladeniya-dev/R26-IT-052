from fastapi import FastAPI
from app.database import engine
from app.models import Base

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Fashion Assistant - Chala Backend",
    description="Backend for Login, Registration, Onboarding, User Profile, and User Learning Engine",
    version="1.0.0"
)


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
        "module": "user-profiling-chalani"
    }
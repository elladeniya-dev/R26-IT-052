from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base, User
from app.schemas import GoogleLoginRequest, GoogleLoginResponse
from app.auth import verify_google_token, create_access_token

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Fashion Assistant - Chala Backend",
    description="Backend for Google Sign-In, Onboarding, User Profile, and User Learning Engine",
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


@app.post("/auth/google", response_model=GoogleLoginResponse)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Google Sign-In endpoint.

    Frontend/mobile app sends Google ID token here.
    Backend verifies the token.
    Then backend creates/fetches user from PostgreSQL.
    Finally backend returns our own JWT token.
    """

    google_user = verify_google_token(request.token)

    existing_user = db.query(User).filter(
        User.google_sub == google_user["google_sub"]
    ).first()

    if existing_user:
        user = existing_user
    else:
        user = User(
            google_sub=google_user["google_sub"],
            full_name=google_user["full_name"],
            email=google_user["email"],
            profile_picture=google_user["profile_picture"],
            auth_provider="google"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "email": user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@app.get("/google-test.html")
def google_test_page():
    return FileResponse("google-test.html")
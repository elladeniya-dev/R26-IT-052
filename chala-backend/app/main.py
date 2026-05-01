from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base, User, UserOnboardingPreference, UserLearnedPreference
from app.schemas import (
    GoogleLoginRequest,
    GoogleLoginResponse,
    OnboardingRequest,
    OnboardingResponse,
    ProfileResponse
)
from app.auth import verify_google_token, create_access_token, get_current_user

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


@app.get("/auth/me")
def get_logged_in_user(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "auth_provider": current_user.auth_provider
    }

@app.post("/onboarding", response_model=OnboardingResponse)
def save_onboarding_preferences(
    request: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves or updates onboarding preferences for the logged-in user.
    The user_id is taken from the JWT token, not from the request body.
    """

    existing_preferences = db.query(UserOnboardingPreference).filter(
        UserOnboardingPreference.user_id == current_user.user_id
    ).first()

    if existing_preferences:
        existing_preferences.preferred_categories = request.preferred_categories
        existing_preferences.preferred_colors = request.preferred_colors
        existing_preferences.preferred_styles = request.preferred_styles
        existing_preferences.price_min = request.price_min
        existing_preferences.price_max = request.price_max
        existing_preferences.occasions = request.occasions
        existing_preferences.preferred_patterns = request.preferred_patterns
        existing_preferences.extra_preferences = request.extra_preferences

        db.commit()
        db.refresh(existing_preferences)

        return existing_preferences

    new_preferences = UserOnboardingPreference(
        user_id=current_user.user_id,
        preferred_categories=request.preferred_categories,
        preferred_colors=request.preferred_colors,
        preferred_styles=request.preferred_styles,
        price_min=request.price_min,
        price_max=request.price_max,
        occasions=request.occasions,
        preferred_patterns=request.preferred_patterns,
        extra_preferences=request.extra_preferences
    )

    db.add(new_preferences)
    db.commit()
    db.refresh(new_preferences)

    return new_preferences


@app.get("/profile", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the logged-in user's profile, onboarding preferences,
    and learned preferences.
    """

    onboarding_preferences = db.query(UserOnboardingPreference).filter(
        UserOnboardingPreference.user_id == current_user.user_id
    ).first()

    learned_preferences = db.query(UserLearnedPreference).filter(
        UserLearnedPreference.user_id == current_user.user_id
    ).first()

    return {
        "user": current_user,
        "onboarding_preferences": onboarding_preferences,
        "learned_preferences": learned_preferences
    }




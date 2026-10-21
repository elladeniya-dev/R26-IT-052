import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    User,
    UserOnboardingPreference,
    UserLearnedPreference,
    UserInteraction,
)

from app.schemas import (
    GoogleLoginRequest,
    GoogleLoginResponse,
)

from app.auth import (
    verify_google_token,
    create_access_token,
    get_current_user,
)


router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# GOOGLE AUTHENTICATION
# ============================================================

@router.post(
    "/auth/google",
    response_model=GoogleLoginResponse,
)
def google_login(
    request: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    google_user = verify_google_token(
        request.token
    )

    existing_user = (
        db.query(User)
        .filter(
            User.google_sub
            == google_user["google_sub"]
        )
        .first()
    )

    if existing_user:
        user = existing_user

    else:
        user = User(
            google_sub=google_user[
                "google_sub"
            ],
            full_name=google_user[
                "full_name"
            ],
            email=google_user[
                "email"
            ],
            profile_picture=google_user[
                "profile_picture"
            ],
            auth_provider="google",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "email": user.email,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


# ============================================================
# DEV LOGIN (plug and play)
# ============================================================
# Skips Google sign-in for local development. It is OFF unless
# DEV_AUTH_BYPASS=true is set in .env, and it refuses to turn on
# when running on Render (the RENDER env var is always set there).
# Remove the flag (or set it to false) and restart to go back to
# the normal Google flow. Nothing else in the auth flow changes.

DEV_AUTH_BYPASS = (
    os.getenv("DEV_AUTH_BYPASS", "false").strip().lower()
    in ("1", "true", "yes", "on")
)

DEV_USER_SUB = "dev-bypass-user"
DEV_USER_EMAIL = os.getenv(
    "DEV_AUTH_EMAIL", "dev.user@example.com"
)
DEV_USER_NAME = os.getenv(
    "DEV_AUTH_NAME", "Dev User"
)

if DEV_AUTH_BYPASS and os.getenv("RENDER"):
    raise RuntimeError(
        "DEV_AUTH_BYPASS must not be enabled on a deployed "
        "server. Remove it from the environment."
    )

if DEV_AUTH_BYPASS:
    logger.warning(
        "DEV_AUTH_BYPASS is ON: POST /auth/dev-login issues "
        "tokens without Google sign-in. Local use only."
    )


@router.post(
    "/auth/dev-login",
    response_model=GoogleLoginResponse,
)
def dev_login(
    db: Session = Depends(get_db),
):
    if not DEV_AUTH_BYPASS:
        # Looks identical to a route that does not exist.
        raise HTTPException(
            status_code=404,
            detail="Not Found",
        )

    user = (
        db.query(User)
        .filter(User.google_sub == DEV_USER_SUB)
        .first()
    )

    if user is None:
        user = User(
            google_sub=DEV_USER_SUB,
            full_name=DEV_USER_NAME,
            email=DEV_USER_EMAIL,
            profile_picture=None,
            auth_provider="dev",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "email": user.email,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/google-test.html")
def google_test_page():
    return FileResponse(
        "google-test.html"
    )


@router.get("/auth/me")
def get_logged_in_user(
    current_user: User = Depends(
        get_current_user
    ),
):
    return {
        "user_id":
            current_user.user_id,

        "full_name":
            current_user.full_name,

        "email":
            current_user.email,

        "auth_provider":
            current_user.auth_provider,
    }


# ============================================================
# DELETE ACCOUNT
# ============================================================

@router.delete("/account")
def delete_current_user_account(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    user_id = current_user.user_id

    try:


        db.query(
            UserLearnedPreference
        ).filter(
            UserLearnedPreference.user_id
            == user_id
        ).delete(
            synchronize_session=False
        )

        db.query(
            UserInteraction
        ).filter(
            UserInteraction.user_id
            == user_id
        ).delete(
            synchronize_session=False
        )

        db.query(
            UserOnboardingPreference
        ).filter(
            UserOnboardingPreference.user_id
            == user_id
        ).delete(
            synchronize_session=False
        )

        db.query(User).filter(
            User.user_id == user_id
        ).delete(
            synchronize_session=False
        )

        db.commit()

        return {
            "message": (
                "Account and all related data "
                "deleted successfully"
            )
        }

    except Exception:

        db.rollback()
        raise
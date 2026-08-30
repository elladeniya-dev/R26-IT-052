from fastapi import APIRouter, Depends
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
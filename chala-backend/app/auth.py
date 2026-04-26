from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv
from jose import jwt
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status


load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID is missing in .env file")

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is missing in .env file")


def verify_google_token(token: str):
    """
    Verifies the Google ID token sent from frontend/mobile app.

    If the token is valid, Google returns user details like:
    - sub
    - email
    - name
    - picture
    """

    try:
        google_user = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        return {
            "google_sub": google_user.get("sub"),
            "email": google_user.get("email"),
            "full_name": google_user.get("name"),
            "profile_picture": google_user.get("picture")
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )


def create_access_token(data: dict):
    """
    Creates our own backend JWT token.

    This token will be used later for protected APIs like:
    - onboarding
    - profile
    - interactions
    - learning update
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return encoded_jwt
from datetime import datetime, timedelta, timezone
import os
import time

from dotenv import load_dotenv
from jose import jwt, JWTError
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_IOS_CLIENT_ID = os.getenv("GOOGLE_IOS_CLIENT_ID")

GOOGLE_ALLOWED_CLIENT_IDS = [
    client_id
    for client_id in (GOOGLE_CLIENT_ID, GOOGLE_IOS_CLIENT_ID)
    if client_id
]
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

bearer_scheme = HTTPBearer()


if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID is missing in .env file")

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is missing in .env file")


GOOGLE_CERT_FETCH_TIMEOUT_SECONDS = 10


class _FastGoogleAuthRequest(requests.Request):
    """
    google.auth.transport.requests.Request, but with a much shorter
    timeout than the library's own 120s default.

    id_token.verify_oauth2_token -> _fetch_certs calls request(url,
    method="GET") without ever passing a timeout, so it silently
    inherits that 120s default. Combined with a retry, a degraded
    network path could hang a sign-in attempt for minutes before any
    error ever reached the user. This fails fast instead so retries
    actually happen within a few seconds.
    """

    def __call__(self, *args, **kwargs):
        kwargs.setdefault("timeout", GOOGLE_CERT_FETCH_TIMEOUT_SECONDS)
        return super().__call__(*args, **kwargs)


def verify_google_token(token: str):
    """
    Verifies the Google ID token sent from frontend/mobile app.
    """

    clean_token = token.strip()

    last_network_error = None

    # verify_oauth2_token calls out to Google's servers to fetch
    # signing certs, which can fail with transient network errors
    # (timeout, connection reset, SSL EOF) unrelated to the token
    # itself. Retry a few times before giving up, since these clear up
    # on their own. Left uncaught entirely, they crash past the CORS
    # middleware and show up in the browser as a misleading "blocked
    # by CORS policy" error instead of the real network failure. Each
    # attempt is capped at GOOGLE_CERT_FETCH_TIMEOUT_SECONDS (see
    # _FastGoogleAuthRequest) instead of the library's 120s default, so
    # 3 attempts still bound total wait to well under a minute instead
    # of potentially minutes per attempt.
    attempts = 3

    for attempt in range(attempts):
        try:
            google_user = id_token.verify_oauth2_token(
                clean_token,
                _FastGoogleAuthRequest(),
                GOOGLE_ALLOWED_CLIENT_IDS
            )

            return {
                "google_sub": google_user.get("sub"),
                "email": google_user.get("email"),
                "full_name": google_user.get("name"),
                "profile_picture": google_user.get("picture")
            }

        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(error)}"
            )

        except Exception as error:
            last_network_error = error
            if attempt < attempts - 1:
                time.sleep(1)

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Google token verification failed: {str(last_network_error)}"
    )


def create_access_token(data: dict):
    """
    Creates backend JWT token for protected APIs.
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


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Reads JWT token from Authorization header,
    verifies it, extracts user_id, and returns logged-in user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials.strip()

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.user_id == int(user_id)).first()

    if user is None:
        raise credentials_exception

    return user
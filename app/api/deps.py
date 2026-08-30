from fastapi import Header, Query

from app.config import settings
from app.core.exceptions import UnauthorizedError


def pagination(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)) -> dict:
    return {"page": page, "size": size}


def require_admin_key(x_api_key: str = Header(default="")) -> None:
    if not settings.admin_api_key or x_api_key != settings.admin_api_key:
        raise UnauthorizedError("Missing or invalid X-API-Key")

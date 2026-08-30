class AppError(Exception):
    """Base for errors that map onto the {"error": {"code","message"}} envelope."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        if code:
            self.code = code
        super().__init__(message)


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class ProductNotFoundError(NotFoundError):
    code = "PRODUCT_NOT_FOUND"


class BrandNotFoundError(NotFoundError):
    code = "BRAND_NOT_FOUND"


class StaleSnapshotError(AppError):
    """No trend_snapshots row exists yet — compute_trends.py hasn't run."""

    code = "NO_TREND_SNAPSHOT"
    status_code = 503


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    status_code = 401

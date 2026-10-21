from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.exc import TimeoutError as SATimeoutError

from app.api.v1.router import router as v1_router
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.database import SessionLocal
from app.ml.engine import DEFAULT_TRENDNET_PATH
from app.repositories.trend_repo import TrendRepository

configure_logging()

app = FastAPI(
    title="OutfitIQ Trend Analysis Backend",
    description="Sri Lankan fashion trend analysis API.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


log = get_logger("app")


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.middleware("http")
async def reject_nul_characters(request: Request, call_next):
    """Postgres cannot store NUL (0x00); psycopg raises on it, which used to surface as a 500."""
    if "\x00" in request.url.path or b"%00" in request.scope.get("query_string", b"").lower() \
            or b"%00" in request.scope.get("raw_path", b"").lower():
        return _error(400, "BAD_REQUEST", "Request contains an invalid NUL character")
    return await call_next(request)


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return _error(exc.status_code, exc.code, exc.message)


@app.exception_handler(OperationalError)
@app.exception_handler(InterfaceError)
@app.exception_handler(SATimeoutError)
def handle_database_unavailable(request: Request, exc: Exception) -> JSONResponse:
    """Database unreachable, dropped or saturated: a retryable 503, not an opaque 500."""
    log.error("database_unavailable", path=request.url.path, error=type(exc).__name__)
    return _error(503, "DATABASE_UNAVAILABLE", "The trend database is temporarily unavailable. Please retry shortly.")


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    log.error("unhandled_error", path=request.url.path, error=type(exc).__name__, detail=str(exc)[:300])
    return _error(500, "INTERNAL_ERROR", "Something went wrong on our side.")


app.include_router(v1_router)


@app.get("/health")
def health():
    """Liveness — no DB."""
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    """DB reachable, model loaded, snapshot freshness."""
    db_ok = True
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception:
        db_ok = False

    model_loaded = Path(DEFAULT_TRENDNET_PATH).exists()

    latest_snapshot_date = None
    is_stale = True  # no readable snapshot is treated as stale, not "fresh"
    if db_ok:
        db = SessionLocal()
        try:
            snapshot = TrendRepository(db).get_latest_snapshot(horizon_days=3)
            if snapshot:
                latest_snapshot_date = str(snapshot.as_of_date)
                is_stale = (date.today() - snapshot.as_of_date).days > 1
        except Exception:
            # e.g. trend_snapshots doesn't exist yet (migrations not run) —
            # a real "not ready" state, not a 500.
            pass
        finally:
            db.close()

    status = "ok" if (db_ok and model_loaded and not is_stale) else "degraded"
    return {
        "status": status,
        "database": db_ok,
        "model_loaded": model_loaded,
        "model_name": "trendnet+mrtf" if model_loaded else "mrtf",
        "latest_snapshot_date": latest_snapshot_date,
        "is_stale": is_stale,
    }

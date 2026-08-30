from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import router as v1_router
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.database import SessionLocal
from app.repositories.trend_repo import TrendRepository

configure_logging()

app = FastAPI(
    title="OutfitIQ Trend Analysis Backend",
    description="Layered FastAPI service — see architecture spec for design rationale.",
    version="2.0.0",
)


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


app.include_router(v1_router)


@app.get("/health")
def health():
    """Liveness — no DB."""
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    """DB reachable, model loaded, data freshness. Must fail loudly if the
    model file is missing — without it the engine silently degrades from
    IC +0.240 to +0.077 (architecture spec §4.5)."""
    db_ok = True
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception:
        db_ok = False

    model_path = Path("app/ml/weights/outfitiq_trendnet.pt")
    model_loaded = model_path.exists()

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

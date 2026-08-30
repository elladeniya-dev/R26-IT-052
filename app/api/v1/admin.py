from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin_key
from app.database import get_db
from app.repositories.run_repo import RunRepository
from app.services.trend_service import TrendService

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin_key)])


@router.post("/compute")
def force_compute(horizon: int = 3, db: Session = Depends(get_db)):
    result = TrendService(db).compute_snapshot(horizon_days=horizon)
    return {"data": result}


@router.get("/runs")
def get_runs(run_date: date | None = None, db: Session = Depends(get_db)):
    runs = RunRepository(db).get_runs(run_date)
    data = [
        {
            "run_id": r.run_id, "run_date": r.run_date, "brand_id": r.brand_id,
            "status": r.status, "products_seen": r.products_seen,
            "products_kept": r.products_kept, "error_message": r.error_message,
        }
        for r in runs
    ]
    return {"data": data, "meta": {"total": len(data)}}


@router.get("/dropped")
def get_dropped(run_date: date | None = None, db: Session = Depends(get_db)):
    rows = RunRepository(db).get_dropped(run_date)
    data = [
        {"id": d.id, "run_date": d.run_date, "brand_id": d.brand_id, "reason": d.reason, "raw_title": d.raw_title}
        for d in rows
    ]
    return {"data": data, "meta": {"total": len(data)}}

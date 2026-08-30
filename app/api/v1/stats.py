from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    return {"data": StatsService(db).overview()}


@router.get("/attributes/{attr_type}")
def attribute_distribution(attr_type: str, db: Session = Depends(get_db)):
    data = StatsService(db).attribute_distribution(attr_type)
    return {"data": data, "meta": {"total": len(data)}}

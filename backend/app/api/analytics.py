"""Analytics API (spec 35-36, 63)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.api import AnalyticsOverview
from ..services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(db: Session = Depends(get_db)):
    return analytics_service.overview(db)


@router.get("/productivity")
def productivity(db: Session = Depends(get_db)):
    return {"items": analytics_service.productivity_detail(db)}

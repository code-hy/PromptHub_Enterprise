"""Audit log API (spec 34, 64)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.api import AuditListResponse
from ..services import audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditListResponse)
def list_audit(
    event_type: str | None = None,
    entity_type: str | None = None,
    entity_ref: str | None = None,
    actor: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = audit_service.list_events(
        db,
        event_type=event_type,
        entity_type=entity_type,
        entity_ref=entity_ref,
        actor=actor,
        limit=limit,
        offset=offset,
    )
    return AuditListResponse(items=items, total=total)


@router.get("/recent")
def recent(db: Session = Depends(get_db), limit: int = Query(25, ge=1, le=100)):
    items = audit_service.recent(db, limit=limit)
    return {"items": items}

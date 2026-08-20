"""Audit event recording (spec section 34)."""

from sqlalchemy.orm import Session

from ..ids import next_event_id
from ..models import AuditEvent, User


def record(
    db: Session,
    event_type: str,
    actor: User | None,
    entity_type: str = "",
    entity_ref: str = "",
    entity_name: str = "",
    details: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_id=next_event_id(db),
        event_type=event_type,
        actor=actor.display_name if actor else "system",
        actor_user_id=actor.id if actor else None,
        entity_type=entity_type,
        entity_ref=entity_ref,
        entity_name=entity_name,
        details=details or {},
    )
    db.add(event)
    db.flush()
    return event


def list_events(
    db: Session,
    *,
    event_type: str | None = None,
    entity_type: str | None = None,
    entity_ref: str | None = None,
    limit: int = 100,
    offset: int = 0,
    actor: str | None = None,
) -> tuple[list[AuditEvent], int]:
    query = db.query(AuditEvent)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_ref:
        query = query.filter(AuditEvent.entity_ref == entity_ref)
    if actor:
        query = query.filter(AuditEvent.actor.ilike(f"%{actor}%"))
    total = query.count()
    items = query.order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset).all()
    return items, total


def recent(db: Session, limit: int = 25) -> list[AuditEvent]:
    return db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit).all()

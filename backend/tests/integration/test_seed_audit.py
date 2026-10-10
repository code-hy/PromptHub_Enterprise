"""Seed audit trail — pre-populated demo history + idempotency."""

from sqlalchemy import func, select

from app.models import AuditEvent
from app.seed import seed_all


def _audit_count(db) -> int:
    return db.scalar(select(func.count()).select_from(AuditEvent)) or 0


def test_seed_audit_trail_populated(db):
    # 8 users + 16 docs + 68 PROMPT_CREATED + lifecycle
    # (60 submitted + 56 approved + 48 published + 4 deprecated)
    # + 5 workflows + 5 policies = 270 seed events (runtime rows only add more).
    assert _audit_count(db) >= 250


def test_seed_audit_trail_covers_lifecycle(db):
    types = {t for (t,) in db.query(AuditEvent.event_type).distinct()}
    for expected in (
        "USER_CREATED",
        "DOCUMENT_INGESTED",
        "PROMPT_CREATED",
        "PROMPT_SUBMITTED",
        "PROMPT_APPROVED",
        "PROMPT_PUBLISHED",
        "PROMPT_DEPRECATED",
        "WORKFLOW_CREATED",
        "POLICY_CREATED",
    ):
        assert expected in types


def test_seed_audit_idempotent(db):
    before = _audit_count(db)
    seed_all()  # already seeded → early return, no duplicate audit rows
    db.expire_all()
    assert _audit_count(db) == before


def test_seed_audit_endpoint_backfills(client):
    # Live scenario: DB seeded before audit seeding existed → endpoint backfills
    # idempotently (second call reports already_seeded with stable count).
    first = client.post("/api/v1/admin/seed-audit").json()
    assert first["audit_events"] >= 250
    second = client.post("/api/v1/admin/seed-audit").json()
    assert second["status"] == "already_seeded"
    assert second["audit_events"] == first["audit_events"]

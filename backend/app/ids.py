"""Business-formatted identifier generation backed by a counter table."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import SQLiteSequence

PREFIXES = {
    "prompt": ("PROMPT", 6),
    "execution": ("EXEC", 8),
    "workflow": ("WORKFLOW", 6),
    "workflow_execution": ("WRUN", 8),
    "policy": ("POLICY", 5),
    "approval": ("APPROVAL", 5),
    "audit": ("EVT", 8),
    "document": ("DOC", 6),
    "user": ("USER", 4),
    "violation": ("VIO", 6),
}


def next_sequential_id(db: Session, counter_type: str) -> str:
    prefix, width = PREFIXES[counter_type]
    seq = db.scalar(select(SQLiteSequence).where(SQLiteSequence.counter_type == counter_type))
    if seq is None:
        seq = SQLiteSequence(counter_type=counter_type, next_value=1)
        db.add(seq)
        db.flush()
    value = seq.next_value
    seq.next_value += 1
    db.flush()
    return f"{prefix}-{value:0{width}d}"


def next_prompt_id(db: Session) -> str:
    return next_sequential_id(db, "prompt")


def next_execution_id(db: Session) -> str:
    return next_sequential_id(db, "execution")


def next_workflow_id(db: Session) -> str:
    return next_sequential_id(db, "workflow")


def next_workflow_execution_id(db: Session) -> str:
    return next_sequential_id(db, "workflow_execution")


def next_policy_id(db: Session) -> str:
    return next_sequential_id(db, "policy")


def next_approval_id(db: Session) -> str:
    return next_sequential_id(db, "approval")


def next_event_id(db: Session) -> str:
    return next_sequential_id(db, "audit")


def next_document_id(db: Session) -> str:
    return next_sequential_id(db, "document")


def next_user_id(db: Session) -> str:
    return next_sequential_id(db, "user")


def next_violation_id(db: Session) -> str:
    return next_sequential_id(db, "violation")

"""Prompt lifecycle actions shared by the prompts router.

Implements the state machine from spec section 28:
DRAFT -> SUBMITTED -> UNDER_REVIEW -> APPROVED -> PUBLISHED -> DEPRECATED -> RETIRED.
No silent changes after publication: publishing snapshots the current version.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..ids import next_approval_id
from ..models import ApprovalRequest, Prompt, PromptVersion, User
from ..services import audit_service


def _snapshot(prompt: Prompt) -> dict:
    return {
        "name": prompt.name,
        "description": prompt.description,
        "goal": prompt.goal,
        "context": prompt.context,
        "source": prompt.source,
        "expectations": prompt.expectations,
        "prompt_template": prompt.prompt_template,
        "business_function": prompt.business_function,
        "application": prompt.application,
        "task": prompt.task,
        "data_classification": prompt.data_classification,
        "risk_level": prompt.risk_level,
        "quality_score": prompt.quality_score,
    }


def submit_for_review(db: Session, prompt: Prompt, user: User, note: str = "") -> Prompt:
    prompt.status = "UNDER_REVIEW"
    if prompt.requires_approval or prompt.risk_level in ("HIGH", "CRITICAL"):
        pending = next_approval_id(db)
        db.add(
            ApprovalRequest(
                request_id=pending,
                prompt_id=prompt.id,
                version=prompt.version,
                requested_by=user.id,
                reason=note or "Submitted for governance approval",
                status="PENDING",
            )
        )
    audit_service.record(
        db,
        "PROMPT_SUBMITTED",
        user,
        entity_type="PROMPT",
        entity_ref=prompt.prompt_id,
        entity_name=prompt.name,
        details={"note": note},
    )
    db.commit()
    db.refresh(prompt)
    return prompt


def approve(db: Session, prompt: Prompt, user: User, note: str = "") -> Prompt:
    prompt.status = "APPROVED"
    _record_approval(db, prompt, user, note, "PROMPT_APPROVED")
    db.commit()
    db.refresh(prompt)
    return prompt


def reject(db: Session, prompt: Prompt, user: User, note: str = "") -> Prompt:
    prompt.status = "CHANGES_REQUIRED"
    _record_approval(db, prompt, user, note, "PROMPT_REJECTED")
    db.commit()
    db.refresh(prompt)
    return prompt


def publish(db: Session, prompt: Prompt, user: User, note: str = "") -> Prompt:
    """Publish — immutable snapshot of the current text; later edits create -
    new versions rather than silently changing the live prompt."""
    prompt.status = "PUBLISHED"
    prompt.published_at = prompt.published_at or __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )
    latest_version = (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt.id)
        .order_by(PromptVersion.version_number.desc())
        .first()
    )
    if latest_version and latest_version.approval_status != "APPROVED":
        latest_version.approval_status = "APPROVED"
        latest_version.approved_by = user.id
    else:
        version = (
            db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt.id, PromptVersion.version == prompt.version)
            .first()
        )
        if version:
            version.approval_status = "APPROVED"
            version.approved_by = user.id

    audit_service.record(
        db,
        "PROMPT_PUBLISHED",
        user,
        entity_type="PROMPT",
        entity_ref=prompt.prompt_id,
        entity_name=prompt.name,
        details={"note": note, "version": prompt.version},
    )
    db.commit()
    db.refresh(prompt)
    return prompt


def deprecate(db: Session, prompt: Prompt, user: User, note: str = "") -> Prompt:
    prompt.status = "DEPRECATED"
    audit_service.record(
        db,
        "PROMPT_DEPRECATED",
        user,
        entity_type="PROMPT",
        entity_ref=prompt.prompt_id,
        entity_name=prompt.name,
        details={"note": note},
    )
    db.commit()
    db.refresh(prompt)
    return prompt


def retire(db: Session, prompt: Prompt, user: User, note: str = "") -> Prompt:
    prompt.status = "RETIRED"
    audit_service.record(
        db,
        "PROMPT_RETIRED",
        user,
        entity_type="PROMPT",
        entity_ref=prompt.prompt_id,
        entity_name=prompt.name,
        details={"note": note},
    )
    db.commit()
    db.refresh(prompt)
    return prompt


def _record_approval(db: Session, prompt: Prompt, user: User, note: str, event: str) -> None:
    pending = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.prompt_id == prompt.id, ApprovalRequest.status == "PENDING")
        .first()
    )
    if pending:
        pending.status = "APPROVED" if event == "PROMPT_APPROVED" else "REJECTED"
        pending.decided_by = user.id
        pending.decision_notes = note
    audit_service.record(
        db,
        event,
        user,
        entity_type="PROMPT",
        entity_ref=prompt.prompt_id,
        entity_name=prompt.name,
        details={"note": note, "version": prompt.version},
    )

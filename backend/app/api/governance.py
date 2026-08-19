"""Governance API (spec 46)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas.api import (
    GovernanceEvaluationIn,
    GovernanceEvaluationOut,
    PolicyIn,
    PolicyOut,
)
from ..security import get_current_user, require_role
from ..services import governance_service

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/policies", response_model=list[PolicyOut])
def list_policies(db: Session = Depends(get_db)):
    return governance_service.list_policies(db)


@router.post("/policies", response_model=PolicyOut)
def create_policy(
    data: PolicyIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("GOVERNANCE", "ADMIN")),
):
    return governance_service.create_policy(db, data, user)


@router.post("/evaluate", response_model=GovernanceEvaluationOut)
def evaluate(
    data: GovernanceEvaluationIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return governance_service.evaluate_governance(db, data, actor=user)


@router.get("/violations")
def list_violations(db: Session = Depends(get_db)):
    from ..models import ComplianceViolation

    items = (
        db.query(ComplianceViolation)
        .order_by(ComplianceViolation.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "items": [
            {
                "id": v.id,
                "violation_id": v.violation_id,
                "policy_id": v.policy_id,
                "message": v.message,
                "severity": v.severity,
                "created_at": v.created_at,
            }
            for v in items
        ]
    }


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return governance_service.governance_summary(db)


@router.post("/scan")
def scan_prompt(text: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    findings = governance_service.scan_prompt_security(text)
    return {"findings": findings, "safe": len(findings) == 0}

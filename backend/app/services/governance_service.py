"""Governance services — policy rules engine, evaluation, classification
checking, injection/sensitive-data detection (spec 31-33, 46)."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from ..config import settings
from ..ids import next_policy_id, next_violation_id
from ..models import ComplianceViolation, GovernancePolicy, Prompt, User
from ..schemas.api import GovernanceEvaluationIn, GovernanceEvaluationOut, PolicyIn
from . import audit_service

# --- Security scanning ------------------------------------------------------

INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous |prior )?instructions",
    r"reveal (the |your )?(system prompt|instructions|system message)",
    r"disregard (the |your |any )?security policy",
    r"forget (everything|all previous)",
    r"you are now (the|demo)? ?(a |an |an editable|a test )?model",
    r"act as (if )?(you were|you are) .*(without any restrictions|unfiltered)",
    r"override (your |the )?(safety|security|guidelines)",
]

SENSITIVE_DATA_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"(\+?[\d][\d\s\-\(\)]{7,})",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "api_key": r"(sk|pk|AIza)[-_a-zA-Z0-9]{16,}",
    "password": r"(?i)(password|passwd|pwd)[=:]\s*\S{4,}",
    "account_number": r"\b\d{8,}\b",
}


def scan_prompt_security(text: str) -> list[dict]:
    findings: list[dict] = []
    lowered = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            findings.append({"category": "prompt_injection", "detail": pattern, "severity": "HIGH"})
            break

    for label, pattern in SENSITIVE_DATA_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            findings.append(
                {"category": f"sensitive_{label}", "detail": matches[0], "severity": "MEDIUM"}
            )
    return findings


# --- Policy engine -----------------------------------------------------------


def _matches_condition(condition: dict, subject: dict) -> bool:
    field = condition.get("field")
    operator = condition.get("operator", "=")
    value = condition.get("value")
    actual = subject.get(field)
    if actual is None:
        return False
    if operator in ("=", "==", "eq"):
        return str(actual) == str(value)
    if operator in ("!=", "neq"):
        return str(actual) != str(value)
    if operator == "in":
        return str(actual) in [str(v) for v in (value or [])]
    if operator == "contains":
        return str(value) in str(actual)
    return False


def evaluate_policy_action(action: dict, decisions: list[dict]) -> None:
    """Merge an IF-THEN policy action into the decision set."""
    action_type = action.get("type")
    label = action.get("label") or action_type
    for existing in decisions:
        if existing.get("type") == action_type:
            return
    decisions.append({"type": action_type, "label": label, "value": action.get("value", True)})


def evaluate_governance(
    db: Session,
    payload: GovernanceEvaluationIn,
    *,
    record_violations: bool = True,
    actor: User | None = None,
) -> GovernanceEvaluationOut:
    subject = payload.model_dump()
    policies = db.query(GovernancePolicy).filter(GovernancePolicy.enabled.is_(True)).all()
    decisions: list[dict] = []
    violations: list[dict] = []

    # Static rules independent of policy rows (spec 32).
    if subject["data_classification"] == "RESTRICTED":
        decisions.append(
            {"type": "deny_external_llm", "label": "External LLM denied", "value": True}
        )
        decisions.append({"type": "require_approval", "label": "Approval required", "value": True})
    if subject["risk_level"] in ("HIGH", "CRITICAL"):
        decisions.append(
            {"type": "require_review", "label": "Human review required", "value": True}
        )
    if subject["contains_pii"]:
        decisions.append({"type": "high_logging", "label": "Enhanced logging", "value": True})
    if subject["external_sharing"] == "ALLOWED" and subject["data_classification"] in (
        "RESTRICTED",
        "CONFIDENTIAL",
    ):
        violations.append(
            {
                "policy": "DATA_EXPORT",
                "message": "External sharing is prohibited for CONFIDENTIAL / RESTRICTED data.",
                "severity": "HIGH",
            }
        )

    for policy in policies:
        if _matches_condition(policy.condition, subject):
            evaluate_policy_action(policy.action, decisions)
            severity = policy.severity
            if policy.action.get("type") in ("deny", "deny_external_llm", "block"):
                violations.append(
                    {
                        "policy": policy.policy_id,
                        "message": policy.description or policy.name,
                        "severity": severity,
                        "condition": policy.condition,
                        "action": policy.action,
                    }
                )

    approved = not any(v.get("severity") in ("HIGH", "CRITICAL") for v in violations)

    if record_violations:
        for violation in violations:
            db.add(
                ComplianceViolation(
                    violation_id=next_violation_id(db),
                    policy_id=violation.get("policy", ""),
                    message=violation.get("message", ""),
                    severity=violation.get("severity", "MEDIUM"),
                )
            )
            if actor is not None:
                audit_service.record(
                    db,
                    "GOVERNANCE_VIOLATION",
                    actor,
                    entity_type="PROMPT",
                    details={
                        "policy": violation.get("policy"),
                        "message": violation.get("message"),
                    },
                )
        db.commit()

    return GovernanceEvaluationOut(approved=approved, violations=violations, decisions=decisions)


def evaluate_prompt_governance(db: Session, prompt: Prompt, actor: User | None = None):
    payload = GovernanceEvaluationIn(
        data_classification=prompt.data_classification,
        risk_level=prompt.risk_level,
        contains_pii=prompt.contains_pii,
        contains_financial_data=prompt.contains_financial_data,
        contains_customer_data=prompt.contains_customer_data,
        external_sharing=prompt.external_sharing,
        llm_provider=settings.llm_provider,
    )
    return evaluate_governance(db, payload, actor=actor)


# --- Policy CRUD --------------------------------------------------------------


def create_policy(db: Session, data: PolicyIn, user: User) -> GovernancePolicy:
    policy = GovernancePolicy(
        policy_id=next_policy_id(db),
        name=data.name,
        description=data.description,
        condition=data.condition or {},
        action=data.action or {},
        severity=data.severity,
        enabled=data.enabled,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def list_policies(db: Session) -> list[GovernancePolicy]:
    return db.query(GovernancePolicy).order_by(GovernancePolicy.name).all()


def governance_summary(db: Session) -> dict[str, Any]:
    from collections import Counter

    from ..models import ApprovalRequest, Prompt

    prompts = db.query(Prompt).all()
    total = len(prompts)
    published = sum(1 for p in prompts if p.status == "PUBLISHED")
    awaiting = db.query(ApprovalRequest).filter(ApprovalRequest.status == "PENDING").count()
    high_risk = sum(1 for p in prompts if p.risk_level in ("HIGH", "CRITICAL"))
    missing_owner = sum(1 for p in prompts if not p.owner_id)
    deprecated = sum(1 for p in prompts if p.status in ("DEPRECATED", "RETIRED"))

    classifications = [
        {"name": name, "count": count}
        for name, count in Counter(p.data_classification for p in prompts).most_common()
    ]
    risks = [
        {"name": name, "count": count}
        for name, count in Counter(p.risk_level for p in prompts).most_common()
    ]
    violations = [
        {
            "id": v.id,
            "violation_id": v.violation_id,
            "policy_id": v.policy_id,
            "message": v.message,
            "severity": v.severity,
            "created_at": v.created_at,
        }
        for v in db.query(ComplianceViolation)
        .order_by(ComplianceViolation.created_at.desc())
        .limit(20)
        .all()
    ]
    return {
        "total_prompts": total,
        "published": published,
        "awaiting_approval": awaiting,
        "high_risk": high_risk,
        "missing_owner": missing_owner,
        "deprecated": deprecated,
        "classifications": classifications,
        "risk_distribution": risks,
        "violations": violations,
    }

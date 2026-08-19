"""Governance policy seed data (spec 32)."""

POLICIES: list[dict] = [
    {
        "name": "Restricted data must stay local",
        "description": "RESTRICTED data must not be sent to external LLM providers and requires approval.",
        "condition": {"field": "data_classification", "operator": "=", "value": "RESTRICTED"},
        "action": {"type": "deny_external_llm", "label": "External LLM denied", "value": True},
        "severity": "HIGH",
    },
    {
        "name": "High risk prompts require review",
        "description": "Prompts classified HIGH or CRITICAL risk require human review before execution.",
        "condition": {"field": "risk_level", "operator": "in", "value": ["HIGH", "CRITICAL"]},
        "action": {"type": "require_review", "label": "Human review required", "value": True},
        "severity": "MEDIUM",
    },
    {
        "name": "PII triggers enhanced logging",
        "description": "Prompts that may contain personal information must have enhanced logging.",
        "condition": {"field": "contains_pii", "operator": "=", "value": True},
        "action": {"type": "high_logging", "label": "Enhanced logging", "value": True},
        "severity": "LOW",
    },
    {
        "name": "Confidential data cannot be shared externally",
        "description": "CONFIDENTIAL and RESTRICTED prompts must prohibit external sharing.",
        "condition": {
            "field": "data_classification",
            "operator": "in",
            "value": ["CONFIDENTIAL", "RESTRICTED"],
        },
        "action": {"type": "prohibit_share", "label": "External sharing prohibited", "value": True},
        "severity": "MEDIUM",
    },
    {
        "name": "Customer data requires evidence",
        "description": "Prompts touching customer data must require evidence and citation of sources.",
        "condition": {"field": "contains_customer_data", "operator": "=", "value": True},
        "action": {"type": "require_evidence", "label": "Evidence required", "value": True},
        "severity": "MEDIUM",
    },
]

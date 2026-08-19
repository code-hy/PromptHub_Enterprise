"""Canonical enumerated values used across PromptHub Enterprise.

Stored as readable strings so values survive SQLite <-> PostgreSQL moves and
render directly in the UI. This module is the single vocabulary contract for
the data model, quality engine, governance rules and the frontend.
"""

from enum import StrEnum


class Role(StrEnum):
    USER = "USER"
    AUTHOR = "AUTHOR"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"
    GOVERNANCE = "GOVERNANCE"


class PromptStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CHANGES_REQUIRED = "CHANGES_REQUIRED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class BusinessFunction(StrEnum):
    EXECUTIVE = "EXECUTIVE"
    FINANCE = "FINANCE"
    HR = "HR"
    IT = "IT"
    LEGAL = "LEGAL"
    MARKETING = "MARKETING"
    OPERATIONS = "OPERATIONS"
    PROJECT_MANAGEMENT = "PROJECT_MANAGEMENT"
    SALES = "SALES"
    DATA_ANALYTICS = "DATA_ANALYTICS"
    RISK = "RISK"
    CUSTOMER_SERVICE = "CUSTOMER_SERVICE"


class Application(StrEnum):
    OUTLOOK = "OUTLOOK"
    TEAMS = "TEAMS"
    WORD = "WORD"
    EXCEL = "EXCEL"
    POWERPOINT = "POWERPOINT"
    ONENOTE = "ONENOTE"
    GENERIC_AI = "GENERIC_AI"


class Task(StrEnum):
    ANALYSE = "ANALYSE"
    CLASSIFY = "CLASSIFY"
    CREATE = "CREATE"
    EXTRACT = "EXTRACT"
    SUMMARISE = "SUMMARISE"
    COMPARE = "COMPARE"
    TRANSFORM = "TRANSFORM"
    REWRITE = "REWRITE"
    TRANSLATE = "TRANSLATE"
    RECOMMEND = "RECOMMEND"


class Audience(StrEnum):
    SENIOR_MANAGEMENT = "SENIOR_MANAGEMENT"
    EXECUTIVE = "EXECUTIVE"
    BOARD = "BOARD"
    MANAGEMENT = "MANAGEMENT"
    TEAM = "TEAM"
    TECHNICAL = "TECHNICAL"
    GENERAL = "GENERAL"
    CUSTOMER = "CUSTOMER"


class Tone(StrEnum):
    PROFESSIONAL = "PROFESSIONAL"
    FORMAL = "FORMAL"
    CONCISE = "CONCISE"
    PERSUASIVE = "PERSUASIVE"
    SUPPORTIVE = "SUPPORTIVE"
    ANALYTICAL = "ANALYTICAL"
    FRIENDLY = "FRIENDLY"
    AUTHORITATIVE = "AUTHORITATIVE"


class OutputFormat(StrEnum):
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    HEADLINE_SUMMARY = "HEADLINE_SUMMARY"
    BULLET_POINTS = "BULLET_POINTS"
    TABLE = "TABLE"
    ACTION_ITEMS = "ACTION_ITEMS"
    EMAIL = "EMAIL"
    MEMORANDUM = "MEMORANDUM"
    REPORT = "REPORT"
    PRESENTATION = "PRESENTATION"
    SPEAKER_NOTES = "SPEAKER_NOTES"
    DECK_OUTLINE = "DECK_OUTLINE"
    JSON = "JSON"
    MARKDOWN = "MARKDOWN"
    PARAGRAPHS = "PARAGRAPHS"
    NARRATIVE = "NARRATIVE"
    FREE_TEXT = "FREE_TEXT"


class InputType(StrEnum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    BOOLEAN = "BOOLEAN"
    DOCUMENT = "DOCUMENT"
    IMAGE = "IMAGE"
    JSON = "JSON"
    TABLE = "TABLE"
    LIST = "LIST"


class DataClassification(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExternalSharing(StrEnum):
    ALLOWED = "ALLOWED"
    PROHIBITED = "PROHIBITED"


class ExecutionStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class WorkflowStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class WorkflowStepStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class DocumentType(StrEnum):
    EMAIL = "EMAIL"
    EMAIL_THREAD = "EMAIL_THREAD"
    TEAMS = "TEAMS"
    MEETING = "MEETING"
    WORD = "WORD"
    EXCEL = "EXCEL"
    POWERPOINT = "POWERPOINT"
    DATASET = "DATASET"
    OTHER = "OTHER"


class AuditEventType(StrEnum):
    PROMPT_CREATED = "PROMPT_CREATED"
    PROMPT_EDITED = "PROMPT_EDITED"
    PROMPT_VERSIONED = "PROMPT_VERSIONED"
    PROMPT_TESTED = "PROMPT_TESTED"
    PROMPT_SUBMITTED = "PROMPT_SUBMITTED"
    PROMPT_APPROVED = "PROMPT_APPROVED"
    PROMPT_REJECTED = "PROMPT_REJECTED"
    PROMPT_PUBLISHED = "PROMPT_PUBLISHED"
    PROMPT_DEPRECATED = "PROMPT_DEPRECATED"
    PROMPT_RETIRED = "PROMPT_RETIRED"
    PROMPT_EXECUTED = "PROMPT_EXECUTED"
    PROMPT_SHARED = "PROMPT_SHARED"
    PROMPT_CLONED = "PROMPT_CLONED"
    PROMPT_RATED = "PROMPT_RATED"
    PROMPT_DELETED = "PROMPT_DELETED"
    WORKFLOW_CREATED = "WORKFLOW_CREATED"
    WORKFLOW_UPDATED = "WORKFLOW_UPDATED"
    WORKFLOW_EXECUTED = "WORKFLOW_EXECUTED"
    LOGIN = "LOGIN"
    GOVERNANCE_VIOLATION = "GOVERNANCE_VIOLATION"
    DOCUMENT_INGESTED = "DOCUMENT_INGESTED"
    USER_CREATED = "USER_CREATED"


class GovernanceDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


# --- Catalogue lists used by library filters / builder dropdowns ------------

BUSINESS_FUNCTIONS = [f.value for f in BusinessFunction]
TASKS = [t.value for t in Task]
APPLICATIONS = [a.value for a in Application]
PROMPT_STATUSES = [s.value for s in PromptStatus]
DATA_CLASSIFICATIONS = [c.value for c in DataClassification]
RISK_LEVELS = [r.value for r in RiskLevel]
ROLES = [r.value for r in Role]
INPUT_TYPES = [t.value for t in InputType]
AUDIENCES = [a.value for a in Audience]
TONES = [t.value for t in Tone]
OUTPUT_FORMATS = [f.value for f in OutputFormat]
EVENT_TYPES = [e.value for e in AuditEventType]

"""SQLAlchemy entities for PromptHub Enterprise.

This is the DDL contract of the platform — every table, key, constraint and
relationship lives here. Tables follow the logical model:
user -> prompt -> version/input/review/execution/rating; prompt -> workflow;
prompt -> knowledge_sources; governance + audit complete the picture.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


# ---------------------------------------------------------------------------
# Users / roles
# ---------------------------------------------------------------------------


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(255), default="", unique=True)
    department: Mapped[str] = mapped_column(String(128), default="")
    title: Mapped[str] = mapped_column(String(128), default="")
    role: Mapped[str] = mapped_column(String(32), default="USER", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    password_hash: Mapped[str] = mapped_column(String(255), default="")

    prompts = relationship("Prompt", back_populates="owner")
    ratings = relationship("PromptRating", back_populates="user")
    executions = relationship("PromptExecution", back_populates="user")


# ---------------------------------------------------------------------------
# Prompt core
# ---------------------------------------------------------------------------


class Prompt(Base, TimestampMixin):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", index=True)
    version: Mapped[str] = mapped_column(String(32), default="1.0")
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    business_function: Mapped[str] = mapped_column(String(64), index=True)
    application: Mapped[str] = mapped_column(String(64), index=True)
    task: Mapped[str] = mapped_column(String(32), index=True)

    # Microsoft-style four-part prompt framework
    goal: Mapped[str] = mapped_column(Text, default="")
    context: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(Text, default="")
    expectations: Mapped[str] = mapped_column(Text, default="")

    system_instruction: Mapped[str] = mapped_column(Text, default="")
    prompt_template: Mapped[str] = mapped_column(Text, default="")

    # Expectations detail (Prompt Builder)
    audience: Mapped[str] = mapped_column(String(64), default="GENERAL")
    tone: Mapped[str] = mapped_column(String(32), default="PROFESSIONAL")
    output_format: Mapped[str] = mapped_column(String(64), default="FREE_TEXT")
    max_length: Mapped[str] = mapped_column(String(32), default="")

    # Governance metadata
    data_classification: Mapped[str] = mapped_column(String(32), default="INTERNAL")
    risk_level: Mapped[str] = mapped_column(String(32), default="LOW")
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_financial_data: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_customer_data: Mapped[bool] = mapped_column(Boolean, default=False)
    external_sharing: Mapped[str] = mapped_column(String(32), default="PROHIBITED")

    # LLM / advanced configuration (Prompt Builder advanced section)
    temperature: Mapped[float] = mapped_column(Float, default=0.2)
    require_evidence: Mapped[bool] = mapped_column(Boolean, default=False)
    avoid_unsupported_claims: Mapped[bool] = mapped_column(Boolean, default=False)
    ask_clarification_questions: Mapped[bool] = mapped_column(Boolean, default=False)

    # Productivity estimates in minutes (spec section 36)
    manual_time_minutes: Mapped[float] = mapped_column(Float, default=30.0)
    ai_time_minutes: Mapped[float] = mapped_column(Float, default=5.0)

    quality_score: Mapped[int] = mapped_column(Integer, default=0)

    tags: Mapped[list] = mapped_column(JSON, default=list)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="prompts")
    versions = relationship("PromptVersion", back_populates="prompt", cascade="all, delete-orphan")
    inputs = relationship("PromptInput", back_populates="prompt", cascade="all, delete-orphan")
    executions = relationship("PromptExecution", back_populates="prompt")
    ratings = relationship("PromptRating", back_populates="prompt")
    favourites = relationship("PromptFavourite", back_populates="prompt")
    reviews = relationship("PromptReview", back_populates="prompt")
    knowledge_sources = relationship(
        "KnowledgeSource", back_populates="prompt", cascade="all, delete-orphan"
    )


class PromptVersion(Base, TimestampMixin):
    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("prompt_id", "version_number", name="uq_prompt_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), index=True)
    version: Mapped[str] = mapped_column(String(32))
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    changes: Mapped[str] = mapped_column(Text, default="")
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    approval_status: Mapped[str] = mapped_column(String(32), default="NOT_REQUIRED")
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    prompt = relationship("Prompt", back_populates="versions")


class PromptInput(Base):
    __tablename__ = "prompt_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    input_type: Mapped[str] = mapped_column(String(32), default="TEXT")
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(Text, default="")
    sample_value: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)

    prompt = relationship("Prompt", back_populates="inputs")


class PromptRating(Base, TimestampMixin):
    __tablename__ = "prompt_ratings"
    __table_args__ = (UniqueConstraint("prompt_id", "user_id", name="uq_prompt_rating"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    stars: Mapped[float] = mapped_column(Float, default=5.0)
    useful: Mapped[str] = mapped_column(String(16), default="")  # YES | PARTIALLY | NO
    feedback: Mapped[str] = mapped_column(Text, default="")

    prompt = relationship("Prompt", back_populates="ratings")
    user = relationship("User", back_populates="ratings")


class PromptFavourite(Base, TimestampMixin):
    __tablename__ = "prompt_favourites"
    __table_args__ = (UniqueConstraint("prompt_id", "user_id", name="uq_prompt_favourite"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    prompt = relationship("Prompt", back_populates="favourites")


class PromptShare(Base, TimestampMixin):
    __tablename__ = "prompt_shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), index=True)
    shared_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    shared_with: Mapped[str] = mapped_column(String(32), default="team")  # team | group | user
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")


class PromptReview(Base, TimestampMixin):
    __tablename__ = "prompt_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), index=True)
    version: Mapped[str] = mapped_column(String(32), default="")
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(32), default="PENDING")
    comments: Mapped[str] = mapped_column(Text, default="")

    prompt = relationship("Prompt", back_populates="reviews")


# ---------------------------------------------------------------------------
# Knowledge / RAG
# ---------------------------------------------------------------------------


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    doc_type: Mapped[str] = mapped_column(String(32), default="OTHER", index=True)
    source_app: Mapped[str] = mapped_column(String(64), default="GENERIC_AI")
    department: Mapped[str] = mapped_column(String(64), default="", index=True)
    author: Mapped[str] = mapped_column(String(128), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, default="")
    char_start: Mapped[int] = mapped_column(Integer, default=0)
    char_end: Mapped[int] = mapped_column(Integer, default=0)

    document = relationship("Document", back_populates="chunks")


class KnowledgeSource(Base, TimestampMixin):
    __tablename__ = "knowledge_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(32), default="DOCUMENT")
    reference: Mapped[str] = mapped_column(Text, default="")

    prompt = relationship("Prompt", back_populates="knowledge_sources")


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


class PromptExecution(Base, TimestampMixin):
    __tablename__ = "prompt_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), index=True)
    version: Mapped[str] = mapped_column(String(32), default="1.0")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(32), default="mock")
    model: Mapped[str] = mapped_column(String(64), default="MockAssistant")
    temperature: Mapped[float] = mapped_column(Float, default=0.2)
    input_data: Mapped[dict] = mapped_column(JSON, default=dict)
    output: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    sources_used: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    eval_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str] = mapped_column(Text, default="")
    execution_mode: Mapped[str] = mapped_column(String(32), default="PROMPT")

    prompt = relationship("Prompt", back_populates="executions")
    user = relationship("User", back_populates="executions")


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------


class Workflow(Base, TimestampMixin):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    business_function: Mapped[str] = mapped_column(String(64), default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    estimated_manual_minutes: Mapped[int] = mapped_column(Integer, default=45)
    estimated_ai_minutes: Mapped[int] = mapped_column(Integer, default=5)

    steps = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.sequence",
    )
    executions = relationship(
        "WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan"
    )


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"), index=True
    )
    step_id: Mapped[str] = mapped_column(String(64))
    sequence: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255), default="")
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"))
    input_mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    continue_on_failure: Mapped[bool] = mapped_column(Boolean, default=False)

    workflow = relationship("Workflow", back_populates="steps")


class WorkflowExecution(Base, TimestampMixin):
    __tablename__ = "workflow_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), index=True)
    workflow_name: Mapped[str] = mapped_column(String(255), default="")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="RUNNING", index=True)
    inputs: Mapped[dict] = mapped_column(JSON, default=dict)
    step_results: Mapped[list] = mapped_column(JSON, default=list)
    final_output: Mapped[str] = mapped_column(Text, default="")
    sources_used: Mapped[list] = mapped_column(JSON, default=list)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow = relationship("Workflow", back_populates="executions")


# ---------------------------------------------------------------------------
# Governance
# ---------------------------------------------------------------------------


class GovernancePolicy(Base, TimestampMixin):
    __tablename__ = "governance_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    condition: Mapped[dict] = mapped_column(JSON, default=dict)
    action: Mapped[dict] = mapped_column(JSON, default=dict)
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ApprovalRequest(Base, TimestampMixin):
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), index=True)
    version: Mapped[str] = mapped_column(String(32), default="")
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision_notes: Mapped[str] = mapped_column(Text, default="")

    prompt = relationship("Prompt")


class ComplianceViolation(Base, TimestampMixin):
    __tablename__ = "compliance_violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    violation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    policy_id: Mapped[str] = mapped_column(String(64), default="")
    prompt_id: Mapped[int | None] = mapped_column(ForeignKey("prompts.id"), nullable=True)
    execution_id: Mapped[str] = mapped_column(String(64), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM")


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(48), index=True)
    actor: Mapped[str] = mapped_column(String(128), default="", index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(48), default="", index=True)
    entity_ref: Mapped[str] = mapped_column(String(64), default="", index=True)
    entity_name: Mapped[str] = mapped_column(String(255), default="")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


# ---------------------------------------------------------------------------
# Sequential id support
# ---------------------------------------------------------------------------


class SQLiteSequence(Base):
    """Counter table so business-formatted identifiers are deterministic per type."""

    __tablename__ = "seq_counters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    counter_type: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    next_value: Mapped[int] = mapped_column(Integer, default=1)

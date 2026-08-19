"""Pydantic request/response schemas for the PromptHub REST API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Users / auth
# ---------------------------------------------------------------------------


class UserSummary(ORMModel):
    id: int
    user_id: str
    username: str
    display_name: str
    email: str = ""
    role: str
    department: str = ""
    title: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str = ""


class LoginResponse(BaseModel):
    token: str
    user: UserSummary


# ---------------------------------------------------------------------------
# Catalog metadata (library filters and builder dropdowns)
# ---------------------------------------------------------------------------


class CatalogOut(BaseModel):
    business_functions: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    applications: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    classifications: list[str] = Field(default_factory=list)
    risk_levels: list[str] = Field(default_factory=list)
    input_types: list[str] = Field(default_factory=list)
    audiences: list[str] = Field(default_factory=list)
    tones: list[str] = Field(default_factory=list)
    output_formats: list[str] = Field(default_factory=list)
    event_types: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    models: list[dict[str, Any]] = Field(default_factory=list)
    providers: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


class PromptInputIn(BaseModel):
    name: str
    input_type: str = "TEXT"
    required: bool = True
    description: str = ""
    sample_value: str = ""


class PromptInputOut(ORMModel):
    id: int
    name: str
    input_type: str
    required: bool
    description: str = ""
    sample_value: str = ""
    position: int = 0


class PromptCreate(BaseModel):
    name: str
    description: str = ""
    business_function: str = "GENERIC"
    application: str = "GENERIC_AI"
    task: str = "ANALYSE"
    goal: str = ""
    context: str = ""
    source: str = ""
    expectations: str = ""
    system_instruction: str = ""
    prompt_template: str = ""
    audience: str = "GENERAL"
    tone: str = "PROFESSIONAL"
    output_format: str = "FREE_TEXT"
    max_length: str = ""
    data_classification: str = "INTERNAL"
    risk_level: str = "LOW"
    requires_approval: bool = False
    contains_pii: bool = False
    contains_financial_data: bool = False
    contains_customer_data: bool = False
    external_sharing: str = "PROHIBITED"
    temperature: float = 0.2
    require_evidence: bool = False
    avoid_unsupported_claims: bool = False
    ask_clarification_questions: bool = False
    manual_time_minutes: float = 30.0
    ai_time_minutes: float = 5.0
    tags: list[str] = Field(default_factory=list)
    inputs: list[PromptInputIn] = Field(default_factory=list)
    knowledge_source_document_ids: list[int] = Field(default_factory=list)


class PromptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    business_function: str | None = None
    application: str | None = None
    task: str | None = None
    goal: str | None = None
    context: str | None = None
    source: str | None = None
    expectations: str | None = None
    system_instruction: str | None = None
    prompt_template: str | None = None
    audience: str | None = None
    tone: str | None = None
    output_format: str | None = None
    max_length: str | None = None
    data_classification: str | None = None
    risk_level: str | None = None
    requires_approval: bool | None = None
    contains_pii: bool | None = None
    contains_financial_data: bool | None = None
    contains_customer_data: bool | None = None
    external_sharing: str | None = None
    temperature: float | None = None
    require_evidence: bool | None = None
    avoid_unsupported_claims: bool | None = None
    ask_clarification_questions: bool | None = None
    manual_time_minutes: float | None = None
    ai_time_minutes: float | None = None
    tags: list[str] | None = None
    inputs: list[PromptInputIn] | None = None
    changes: str = ""


class PromptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt_id: str
    name: str
    description: str = ""
    status: str
    version: str
    business_function: str = ""
    application: str = ""
    task: str = ""
    owner_id: int | None = None
    data_classification: str = "INTERNAL"
    risk_level: str = "LOW"
    tags: list[str] = Field(default_factory=list)
    rating_avg: float = 0.0
    rating_count: int = 0
    execution_count: int = 0
    is_favourite: bool = False


class PromptDetail(PromptSummary):
    goal: str = ""
    context: str = ""
    source: str = ""
    expectations: str = ""
    system_instruction: str = ""
    prompt_template: str = ""
    audience: str = ""
    tone: str = ""
    output_format: str = ""
    max_length: str = ""
    contains_pii: bool = False
    contains_financial_data: bool = False
    contains_customer_data: bool = False
    external_sharing: str = ""
    requires_approval: bool = False
    temperature: float = 0.2
    require_evidence: bool = False
    avoid_unsupported_claims: bool = False
    ask_clarification_questions: bool = False
    manual_time_minutes: float = 30.0
    ai_time_minutes: float = 5.0
    quality_score: int = 0
    inputs: list[PromptInputOut] = Field(default_factory=list)
    owner_name: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    published_at: datetime | None = None


class PromptListResponse(BaseModel):
    items: list[PromptSummary]
    total: int
    page: int = 1
    page_size: int = 24


class PromptFlowAction(BaseModel):
    action: str  # publish | deprecate | retire | submit_for_review | approve | reject
    note: str = ""


class RatingCreate(BaseModel):
    stars: float = 5.0
    useful: str = ""  # YES | PARTIALLY | NO
    feedback: str = ""


class RatingOut(ORMModel):
    id: int
    prompt_id: int
    stars: float
    useful: str = ""
    feedback: str = ""
    created_at: datetime | None = None


class CloneCreate(BaseModel):
    name: str | None = None


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------


class VersionOut(ORMModel):
    id: int
    prompt_id: int
    version: str
    version_number: int
    author_id: int | None = None
    changes: str = ""
    approval_status: str = ""
    created_at: datetime | None = None


class VersionDetail(VersionOut):
    snapshot: dict[str, Any] = Field(default_factory=dict)


class VersionCompare(BaseModel):
    from_version: str
    to_version: str
    changes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Assistant
# ---------------------------------------------------------------------------


class AssistantRequest(BaseModel):
    prompt: str
    mode: str = "improve"  # analyse | improve | generate | explain
    business_function: str = ""
    task: str = ""


class AnalysisBreakdown(BaseModel):
    goal: dict[str, int] = Field(default_factory=dict)
    context: dict[str, int] = Field(default_factory=dict)
    source: dict[str, int] = Field(default_factory=dict)
    expectations: dict[str, int] = Field(default_factory=dict)
    specificity: dict[str, int] = Field(default_factory=dict)
    constraints: dict[str, int] = Field(default_factory=dict)
    audience: dict[str, int] = Field(default_factory=dict)
    output_format: dict[str, int] = Field(default_factory=dict)
    examples: dict[str, int] = Field(default_factory=dict)


class AssistantResponse(BaseModel):
    score: int
    rating: str
    breakdown: dict[str, dict[str, int]] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)
    present: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    analysis: list[dict[str, str]] = Field(default_factory=list)
    improved_prompt: str = ""
    generated_prompt: str = ""
    explanation: str = ""


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


class ExecutionRequest(BaseModel):
    prompt_id: int
    input_data: dict[str, Any] = Field(default_factory=dict)
    model_provider: str | None = None
    model_name: str | None = None
    temperature: float | None = None
    document_ids: list[int] = Field(default_factory=list)
    use_grounding: bool = True


class ExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: str
    prompt_id: int
    version: str
    provider: str = ""
    model: str = ""
    status: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output: str = ""
    tokens: int = 0
    latency_ms: int = 0
    sources_used: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    eval_metrics: dict[str, Any] = Field(default_factory=dict)
    error_message: str = ""
    estimated_time_saved_minutes: float = 0.0
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------


class WorkflowStepIn(BaseModel):
    sequence: int
    name: str = ""
    prompt_id: int
    input_mapping: dict[str, str] = Field(default_factory=dict)
    continue_on_failure: bool = False


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    business_function: str = ""
    tags: list[str] = Field(default_factory=list)
    steps: list[WorkflowStepIn] = Field(default_factory=list)


class WorkflowStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    step_id: str
    sequence: int
    name: str = ""
    prompt_id: int
    prompt_name: str = ""
    input_mapping: dict[str, str] = Field(default_factory=dict)
    continue_on_failure: bool = False


class WorkflowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: str
    name: str
    description: str = ""
    status: str
    business_function: str = ""
    tags: list[str] = Field(default_factory=list)
    owner_id: int | None = None
    steps: list[WorkflowStepOut] = Field(default_factory=list)
    estimated_manual_minutes: int = 45
    estimated_ai_minutes: int = 5
    created_at: datetime | None = None


class WorkflowListResponse(BaseModel):
    items: list[WorkflowOut]
    total: int


class WorkflowRunRequest(BaseModel):
    input_data: dict[str, Any] = Field(default_factory=dict)
    document_ids: list[int] = Field(default_factory=list)


class WorkflowExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    execution_id: str
    workflow_name: str = ""
    status: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    step_results: list[dict[str, Any]] = Field(default_factory=list)
    final_output: str = ""
    sources_used: list[str] = Field(default_factory=list)
    latency_ms: int = 0
    error_message: str = ""
    created_at: datetime | None = None
    ended_at: datetime | None = None


# ---------------------------------------------------------------------------
# Governance
# ---------------------------------------------------------------------------


class PolicyIn(BaseModel):
    name: str
    description: str = ""
    condition: dict[str, Any] = Field(default_factory=dict)
    action: dict[str, Any] = Field(default_factory=dict)
    severity: str = "MEDIUM"
    enabled: bool = True


class PolicyOut(ORMModel):
    id: int
    policy_id: str
    name: str
    description: str = ""
    condition: dict[str, Any] = Field(default_factory=dict)
    action: dict[str, Any] = Field(default_factory=dict)
    severity: str = "MEDIUM"
    enabled: bool = True


class GovernanceEvaluationIn(BaseModel):
    data_classification: str = "INTERNAL"
    risk_level: str = "LOW"
    contains_pii: bool = False
    contains_financial_data: bool = False
    contains_customer_data: bool = False
    external_sharing: str = "PROHIBITED"
    llm_provider: str = "mock"


class GovernanceEvaluationOut(BaseModel):
    approved: bool
    violations: list[dict[str, Any]] = Field(default_factory=list)
    decisions: list[dict[str, Any]] = Field(default_factory=list)


class ReviewIn(BaseModel):
    decision: str  # APPROVED | REJECTED | CHANGES_REQUIRED
    comment: str = ""


class ApprovalIn(BaseModel):
    status: str  # APPROVED | REJECTED
    note: str = ""


class GovernanceSummary(BaseModel):
    total_prompts: int = 0
    published: int = 0
    awaiting_approval: int = 0
    high_risk: int = 0
    missing_owner: int = 0
    deprecated: int = 0
    classifications: list[dict[str, Any]] = Field(default_factory=list)
    risk_distribution: list[dict[str, Any]] = Field(default_factory=list)
    violations: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


class AnalyticsOverview(BaseModel):
    prompt_count: int = 0
    published_count: int = 0
    execution_count: int = 0
    success_rate: float = 0.0
    avg_rating: float = 0.0
    rating_count: int = 0
    estimated_time_saved_minutes: float = 0.0
    avg_latency_ms: float = 0.0
    avg_tokens: int = 0
    top_prompts: list[dict[str, Any]] = Field(default_factory=list)
    execution_by_category: list[dict[str, Any]] = Field(default_factory=list)
    executions_by_day: list[dict[str, Any]] = Field(default_factory=list)
    model_usage: list[dict[str, Any]] = Field(default_factory=list)
    status_distribution: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class AuditEventOut(ORMModel):
    id: int
    event_type: str
    actor: str = ""
    entity_type: str = ""
    entity_ref: str = ""
    entity_name: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class AuditListResponse(BaseModel):
    items: list[AuditEventOut]
    total: int

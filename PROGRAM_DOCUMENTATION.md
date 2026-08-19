# PROGRAM_DOCUMENTATION.md — Module-by-Module Reference

A complete technical reference for every module, file, function, input
parameter, and output in PromptHub Enterprise.

---

## Table of contents

1. [Backend — application core](#1-backend--application-core)
2. [Backend — API routers](#2-backend--api-routers)
3. [Backend — services](#3-backend--services)
4. [Backend — quality engine](#4-backend--quality-engine)
5. [Backend — LLM layer](#5-backend--llm-layer)
6. [Backend — RAG retriever](#6-backend--rag-retriever)
7. [Backend — seed data](#7-backend--seed-data)
8. [Backend — models (ORM entities)](#8-backend--models-orm-entities)
9. [Backend — schemas (Pydantic)](#9-backend--schemas-pydantic)
10. [Backend — enums and constants](#10-backend--enums-and-constants)
11. [Frontend — application core](#11-frontend--application-core)
12. [Frontend — API client](#12-frontend--api-client)
13. [Frontend — shared UI components](#13-frontend--shared-ui-components)
14. [Frontend — pages](#14-frontend-pages)
15. [Infrastructure files](#15-infrastructure-files)

---

## 1. Backend — application core

### 1.1 `backend/app/main.py` — Application entrypoint

**Purpose:** Creates the FastAPI application, registers middleware, includes
all API routers, and runs the startup lifecycle (DB init + seed).

**Inputs (environment variables):** All variables from `config.py`

**Outputs:** `app` — the FastAPI application instance, served by uvicorn

**Key functions:**

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `create_app()` | — | `FastAPI` | Builds the app with CORS, routers, health endpoint |
| `lifespan(app)` | `FastAPI` | async context | On startup: calls `init_db()` then `seed_all()` |

**Routers registered (all under `/api/v1`):**

| Router | Prefix | Tag |
|--------|--------|-----|
| `catalog.router` | `/catalog` | metadata for filters/dropdowns |
| `auth.router` | `/auth` | login, current user |
| `prompts.router` | `/prompts` | CRUD, lifecycle, versions, ratings |
| `assistant.router` | `/assistant` | quality analysis/improve/generate/explain |
| `executions.router` | `/executions` | run prompts, list executions |
| `workflows.router` | `/workflows` | CRUD, run workflows |
| `governance.router` | `/governance` | policies, evaluation, scan, violations |
| `analytics.router` | `/analytics` | overview, trends, categories |
| `audit.router` | `/audit` | audit event log |
| `admin.router` | `/admin` | user management |
| `knowledge.router` | `/knowledge` | document listing |

**Health endpoint:** `GET /health` returns `{"status": "ok", "app": "PromptHub Enterprise", "provider": "mock"}`

---

### 1.2 `backend/app/config.py` — Configuration

**Purpose:** Loads all settings from environment variables or `.env` file.

**Inputs (environment variables):**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_NAME` | str | `"PromptHub Enterprise"` | Application name |
| `APP_ENV` | str | `"development"` | Environment mode |
| `DEBUG` | bool | `True` | Debug mode |
| `API_PREFIX` | str | `"/api/v1"` | URL prefix for all API routes |
| `DATABASE_URL` | str | `""` (empty = SQLite) | Database connection string |
| `LLM_PROVIDER` | str | `"auto"` | LLM provider: auto/mock/ollama/openai/litellm |
| `OLLAMA_BASE_URL` | str | `"http://localhost:11434"` | Ollama server URL |
| `OLLAMA_MODEL` | str | `""` (falls back to `"qwen3:1.7b"`) | Ollama model name |
| `OPENAI_API_KEY` | str | `""` | OpenAI API key |
| `OPENAI_MODEL` | str | `"gpt-4o-mini"` | OpenAI model name |
| `OPENAI_BASE_URL` | str | `""` | OpenAI-compatible base URL |
| `LITELLM_BASE_URL` | str | `"http://localhost:4000"` | LiteLLM gateway URL |
| `LITELLM_MODEL` | str | `""` | LiteLLM model name |
| `RAG_MODE` | str | `"local"` | RAG mode: local or qdrant |
| `QDRANT_URL` | str | `"http://localhost:6333"` | Qdrant server URL |
| `RAG_ENABLED` | bool | `False` | Enable RAG by default |
| `SECRET_KEY` | str | `"change-me-..."` | HMAC signing key for tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `720` | Token TTL in minutes |
| `ENABLE_AUTH` | bool | `False` | Require login (false = auto-login as henry) |
| `CORS_ORIGINS` | str | `"http://localhost:5173,..."` | Allowed CORS origins |
| `MOCK_LLM_LATENCY_MS` | int | `250` | Simulated delay for mock provider |
| `LLM_TIMEOUT_SECONDS` | int | `300` | LLM call timeout |
| `SEED_DEMO_DATA` | bool | `True` | Seed demo data on first boot |
| `SYNTHETIC_M365_SCALE` | str | `"small"` | Document corpus size |
| `DATA_DIR` | str | `"<repo>/data"` | Data directory path |

**Computed properties:**

| Property | Output | Description |
|----------|--------|-------------|
| `sqlalchemy_url` | `str` | Full SQLAlchemy connection URL |
| `cors_origin_list` | `list[str]` | Parsed CORS origins |
| `resolved_ollama_model` | `str` | Ollama model with fallback default |

---

### 1.3 `backend/app/database.py` — Database engine

**Purpose:** Creates the SQLAlchemy engine, session factory, and provides DB initialization/reset functions.

**Inputs:** `settings.sqlalchemy_url` (from config)

**Outputs:**

| Export | Type | Description |
|--------|------|-------------|
| `Base` | `DeclarativeBase` | Base class for all ORM models |
| `engine` | `Engine` | SQLAlchemy engine |
| `SessionLocal` | `sessionmaker` | Session factory |
| `get_db()` | generator | Yields a DB session, auto-closes |
| `init_db()` | None | Creates all tables via `Base.metadata.create_all()` |
| `reset_db()` | None | Drops all tables (tests/reset) |

---

### 1.4 `backend/app/ids.py` — Business ID generation

**Purpose:** Generates sequential, human-readable IDs using a counter table.

**ID formats:**

| Counter type | Prefix | Width | Example |
|-------------|--------|-------|---------|
| `prompt` | `PROMPT` | 6 | `PROMPT-000001` |
| `execution` | `EXEC` | 8 | `EXEC-00000001` |
| `workflow` | `WORKFLOW` | 6 | `WORKFLOW-000001` |
| `workflow_execution` | `WRUN` | 8 | `WRUN-00000001` |
| `policy` | `POLICY` | 5 | `POLICY-00001` |
| `approval` | `APPROVAL` | 5 | `APPROVAL-00001` |
| `audit` | `EVT` | 8 | `EVT-00000001` |
| `document` | `DOC` | 6 | `DOC-000001` |
| `user` | `USER` | 4 | `USER-0001` |
| `violation` | `VIO` | 6 | `VIO-000001` |

**Functions:** `next_sequential_id(db, counter_type)`, `next_prompt_id(db)`, `next_execution_id(db)`, `next_workflow_id(db)`, `next_workflow_execution_id(db)`, `next_policy_id(db)`, `next_approval_id(db)`, `next_event_id(db)`, `next_document_id(db)`, `next_user_id(db)`, `next_violation_id(db)` — all take `Session`, return `str`.

---

### 1.5 `backend/app/security.py` — Authentication

**Purpose:** Password hashing (PBKDF2), token creation/verification (HMAC), and user resolution.

**Functions:**

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `hash_password(password, salt?)` | `str`, optional `bytes` | `str` | Returns `"pbkdf2$<salt>$<hash>"` |
| `verify_password(password, stored)` | `str`, `str` | `bool` | Verifies plaintext against stored hash |
| `create_token(user)` | `User` | `str` | Returns `"userId:dbId:role:timestamp.<hmac>"` |
| `decode_token(token)` | `str` | `dict \| None` | Returns `{"user_id", "id", "role"}` or `None` |
| `get_current_user(credentials?, db)` | Bearer token, `Session` | `User` | Returns demo user if auth disabled, else token identity |
| `require_role(*roles)` | role strings | dependency | Raises 403 if user role not in allowed roles |
| `demo_user(db)` | `Session` | `User` | Returns the `henry` user |

---

### 1.6 `backend/app/core/enums.py` — Enumerations

**Purpose:** Defines all allowed values as string enums. Used across the entire stack.

**Enums defined:**

| Enum | Values | Used for |
|------|--------|----------|
| `Role` | USER, AUTHOR, REVIEWER, ADMIN, GOVERNANCE | User roles |
| `PromptStatus` | DRAFT, SUBMITTED, UNDER_REVIEW, CHANGES_REQUIRED, APPROVED, PUBLISHED, DEPRECATED, RETIRED | Prompt lifecycle |
| `BusinessFunction` | EXECUTIVE, FINANCE, HR, IT, LEGAL, MARKETING, OPERATIONS, PROJECT_MANAGEMENT, SALES, DATA_ANALYTICS, RISK, CUSTOMER_SERVICE | Prompt categorisation |
| `Application` | OUTLOOK, TEAMS, WORD, EXCEL, POWERPOINT, ONENOTE, GENERIC_AI | Target application |
| `Task` | ANALYSE, CLASSIFY, CREATE, EXTRACT, SUMMARISE, COMPARE, TRANSFORM, REWRITE, TRANSLATE, RECOMMEND | Prompt task type |
| `Audience` | SENIOR_MANAGEMENT, EXECUTIVE, BOARD, MANAGEMENT, TEAM, TECHNICAL, GENERAL, CUSTOMER | Target audience |
| `Tone` | PROFESSIONAL, FORMAL, CONCISE, PERSUASIVE, SUPPORTIVE, ANALYTICAL, FRIENDLY, AUTHORITATIVE | Prompt tone |
| `OutputFormat` | EXECUTIVE_SUMMARY, HEADLINE_SUMMARY, BULLET_POINTS, TABLE, ACTION_ITEMS, EMAIL, MEMORANDUM, REPORT, PRESENTATION, SPEAKER_NOTES, DECK_OUTLINE, JSON, MARKDOWN, PARAGRAPHS, NARRATIVE, FREE_TEXT | Expected output format |
| `InputType` | TEXT, NUMBER, DATE, BOOLEAN, DOCUMENT, IMAGE, JSON, TABLE, LIST | Prompt input types |
| `DataClassification` | PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED | Data sensitivity |
| `RiskLevel` | LOW, MEDIUM, HIGH, CRITICAL | Prompt risk |
| `ExternalSharing` | ALLOWED, PROHIBITED | Sharing policy |
| `ExecutionStatus` | PENDING, RUNNING, SUCCESS, FAILED, CANCELLED, BLOCKED | Execution state |
| `WorkflowStatus` | DRAFT, PUBLISHED, DEPRECATED, RETIRED | Workflow state |
| `WorkflowStepStatus` | PENDING, RUNNING, SUCCESS, FAILED, SKIPPED | Step state |
| `DocumentType` | EMAIL, EMAIL_THREAD, TEAMS, MEETING, WORD, EXCEL, POWERPOINT, DATASET, OTHER | Document type |
| `AuditEventType` | 22 values (PROMPT_CREATED through USER_CREATED) | Audit events |
| `GovernanceDecision` | ALLOW, DENY, REQUIRES_REVIEW, REQUIRES_APPROVAL | Governance outcomes |

**Catalogue exports (used by frontend dropdowns):** `BUSINESS_FUNCTIONS`, `TASKS`, `APPLICATIONS`, `PROMPT_STATUSES`, `DATA_CLASSIFICATIONS`, `RISK_LEVELS`, `ROLES`, `INPUT_TYPES`, `AUDIENCES`, `TONES`, `OUTPUT_FORMATS`, `EVENT_TYPES`

---

## 2. Backend — API routers

### 2.1 `backend/app/api/auth.py` — Authentication

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/auth/login` | POST | `LoginRequest {username, password}` | `LoginResponse {token, user}` | No |
| `/auth/me` | GET | — | `UserSummary` | Yes |

### 2.2 `backend/app/api/catalog.py` — Filter metadata

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/catalog` | GET | — | `CatalogOut` | No |

**CatalogOut fields:** `business_functions`, `tasks`, `applications`, `statuses`, `classifications`, `risk_levels`, `input_types`, `audiences`, `tones`, `output_formats`, `event_types`, `roles`, `models`, `providers`

### 2.3 `backend/app/api/prompts.py` — Prompt CRUD + lifecycle

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/prompts` | GET | query: `search`, `business_function`, `application`, `task`, `status`, `risk_level`, `classification`, `tag`, `favourite_only`, `is_template`, `sort`, `page`, `page_size` | `PromptListResponse` | Yes |
| `/prompts` | POST | `PromptCreate` body | `PromptDetail` | Yes |
| `/prompts/{ref}` | GET | path: `prompt_ref` | `PromptDetail` | Yes |
| `/prompts/{ref}` | PUT | path + `PromptUpdate` body | `PromptDetail` | Yes |
| `/prompts/{ref}` | DELETE | path: `prompt_ref` | `{"ok": true}` | ADMIN |
| `/prompts/{ref}/clone` | POST | path + optional `CloneCreate` | `PromptDetail` | Yes |
| `/prompts/{ref}/flow` | POST | path + `PromptFlowAction {action, note?}` | `PromptDetail` | Yes |
| `/prompts/{ref}/rate` | POST | path + `RatingCreate {stars, useful?}` | `RatingOut` | Yes |
| `/prompts/{ref}/favourite` | POST | path | `{"is_favourite": bool}` | Yes |
| `/prompts/{ref}/governance` | GET | path | `{prompt_id, approved, violations, decisions}` | Yes |
| `/prompts/{ref}/versions` | GET | path | `list[VersionOut]` | No |
| `/prompts/{ref}/versions/{v}` | GET | path | `VersionDetail` | No |
| `/prompts/{ref}/compare` | GET | path + query: `from_version`, `to_version` | `VersionCompare` | No |

**Lifecycle flow actions:** `submit_for_review`, `approve`, `reject`, `publish`, `deprecate`, `retire`

### 2.4 `backend/app/api/assistant.py` — Quality analysis

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/assistant/analyse` | POST | `AssistantRequest {prompt, mode?, business_function?, task?}` | `AssistantResponse` | Yes |
| `/assistant/improve` | POST | `AssistantRequest` | `AssistantResponse` | Yes |
| `/assistant/generate` | POST | `AssistantRequest` | `AssistantResponse` | Yes |
| `/assistant/explain` | POST | `AssistantRequest` | `AssistantResponse` | Yes |

### 2.5 `backend/app/api/executions.py` — Prompt execution

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/executions` | POST | `ExecutionRequest {prompt_id, input_data?, model_provider?, model_name?, temperature?, document_ids?, use_grounding?}` | `ExecutionOut` | Yes |
| `/executions` | GET | query: `prompt_id?`, `status?`, `limit`, `offset` | `{items, total}` | No |
| `/executions/{id}` | GET | path: `execution_id` | `ExecutionOut` | No |

### 2.6 `backend/app/api/workflows.py` — Workflow management

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/workflows` | GET | — | `WorkflowListResponse` | No |
| `/workflows` | POST | `WorkflowCreate {name, description?, business_function?, tags?, steps?}` | `WorkflowOut` | Yes |
| `/workflows/{ref}` | GET | path | `WorkflowOut` | No |
| `/workflows/{ref}/run` | POST | path + `WorkflowRunRequest {input_data?, document_ids?}` | `WorkflowExecutionOut` | Yes |
| `/workflows/{ref}/executions` | GET | path | `{items}` | No |

### 2.7 `backend/app/api/governance.py` — Governance

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/governance/policies` | GET | — | `list[PolicyOut]` | No |
| `/governance/policies` | POST | `PolicyIn {name, description?, condition?, action?, severity, enabled}` | `PolicyOut` | GOVERNANCE/ADMIN |
| `/governance/evaluate` | POST | `GovernanceEvaluationIn {data_classification, risk_level, contains_pii, contains_financial_data, contains_customer_data, external_sharing, llm_provider}` | `GovernanceEvaluationOut` | Yes |
| `/governance/violations` | GET | — | `{items}` | No |
| `/governance/summary` | GET | — | `dict` | No |
| `/governance/scan` | POST | query: `text` | `{findings, safe}` | Yes |

### 2.8 `backend/app/api/analytics.py` — Analytics

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/analytics/overview` | GET | — | `AnalyticsOverview` | No |

### 2.9 `backend/app/api/audit.py` — Audit log

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/audit` | GET | query: `event_type?`, `entity_type?`, `actor?`, `entity_ref?`, `limit`, `offset` | `{items, total}` | No |

### 2.10 `backend/app/api/admin.py` — User management

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/admin/users` | GET | — | `list[UserSummary]` | ADMIN |

### 2.11 `backend/app/api/knowledge.py` — Document management

| Endpoint | Method | Input | Output | Auth |
|----------|--------|-------|--------|------|
| `/knowledge/documents` | GET | query: `page`, `page_size` | `{items, total}` | No |

---

## 3. Backend — services

### 3.1 `backend/app/services/prompt_service.py` — Prompt business logic

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `list_prompts(db, search, business_function, application, task, status, risk_level, classification, tag, favourite_only, user_id, is_template, sort, page, page_size)` | `Session`, filters | `PromptListResponse` | Filtered, sorted, paginated prompt list |
| `create_prompt(db, data, user)` | `Session`, `PromptCreate`, `User` | `Prompt` | Creates prompt with ID, version snapshot |
| `update_prompt(db, prompt, data, user, create_version?)` | `Session`, `Prompt`, `PromptUpdate`, `User`, `bool` | `Prompt` | Updates fields, optionally creates version |
| `clone_prompt(db, prompt, user, name?)` | `Session`, `Prompt`, `User`, `str?` | `Prompt` | Deep copy with new ID |
| `get_prompt(db, ref)` | `Session`, `str` | `Prompt \| None` | Lookup by prompt_id or DB id |
| `to_detail(prompt, db, user_id)` | `Prompt`, `Session`, `int` | `PromptDetail` | Full detail with inputs, versions, governance |
| `to_summary(prompt, db, user_id)` | `Prompt`, `Session`, `int` | `PromptSummary` | Lightweight list item |
| `rate_prompt(db, prompt, user, data)` | `Session`, `Prompt`, `User`, `RatingCreate` | `RatingOut` | Upsert rating |
| `toggle_favourite(db, prompt, user)` | `Session`, `Prompt`, `User` | `bool` | Toggle favourite |
| `list_versions(db, prompt)` | `Session`, `Prompt` | `list[VersionOut]` | All versions |
| `get_version(db, prompt, version_ref)` | `Session`, `Prompt`, `str` | `VersionDetail \| None` | Single version |
| `compare_versions(old, new)` | `VersionDetail?`, `VersionDetail?` | `VersionCompare` | Diff between versions |

### 3.2 `backend/app/services/execution_service.py` — Prompt execution

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `run_prompt(db, prompt, user, req)` | `Session`, `Prompt`, `User`, `ExecutionRequest` | `PromptExecution` | Fills template, calls LLM, evaluates, records |
| `to_execution_out(db, execution)` | `Session`, `PromptExecution` | `ExecutionOut` | Serialises execution with eval metrics |
| `list_executions(db, prompt_id?, status?, limit, offset)` | `Session`, filters | `(list, int)` | Paginated execution list |

### 3.3 `backend/app/services/workflow_service.py` — Workflow execution

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `create_workflow(db, data, user)` | `Session`, `WorkflowCreate`, `User` | `Workflow` | Creates workflow with steps |
| `get_workflow(db, ref)` | `Session`, `str` | `Workflow \| None` | Lookup by workflow_id |
| `list_workflows(db)` | `Session` | `(list, int)` | All workflows |
| `run_workflow(db, wf, user, req)` | `Session`, `Workflow`, `User`, `WorkflowRunRequest` | `WorkflowExecution` | Runs all steps sequentially |
| `to_workflow_out(wf)` | `Workflow` | `WorkflowOut` | Serialises workflow with steps |
| `to_workflow_execution_out(exec)` | `WorkflowExecution` | `WorkflowExecutionOut` | Serialises run results |

### 3.4 `backend/app/services/governance_service.py` — Policy engine

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `scan_prompt_security(text)` | `str` | `list[dict]` | Regex-based injection/sensitive-data scan |
| `_matches_condition(condition, subject)` | `dict`, `dict` | `bool` | Tests a policy condition against subject attributes |
| `evaluate_policy_action(action, decisions)` | `dict`, `list[dict]` | None (mutates) | Merges policy action into decision list |
| `evaluate_governance(db, payload, record_violations?, actor?)` | `Session`, `GovernanceEvaluationIn`, `bool`, `User?` | `GovernanceEvaluationOut` | Full policy evaluation |
| `evaluate_prompt_governance(db, prompt, actor?)` | `Session`, `Prompt`, `User?` | `GovernanceEvaluationOut` | Evaluate a saved prompt |
| `create_policy(db, data, user)` | `Session`, `PolicyIn`, `User` | `GovernancePolicy` | Create new policy |
| `list_policies(db)` | `Session` | `list[GovernancePolicy]` | All enabled policies |
| `governance_summary(db)` | `Session` | `dict` | Aggregate stats + violations |

### 3.5 `backend/app/services/assistant_service.py` — Quality analysis

| Function | Input | Output |
|----------|-------|--------|
| `analyse(raw, mode, business_function?, task?)` | `str`, `str`, `str`, `str` | `AssistantResponse` |

**Modes:** `analyse` (score + missing/present + recommendations), `improve` (returns improved_prompt), `generate` (returns generated_prompt), `explain` (returns explanation)

### 3.6 `backend/app/services/lifecycle_service.py` — Prompt state machine

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `submit_for_review(db, prompt, user, note?)` | `Session`, `Prompt`, `User`, `str?` | `Prompt` | DRAFT -> UNDER_REVIEW |
| `approve(db, prompt, user, note?)` | `Session`, `Prompt`, `User`, `str?` | `Prompt` | UNDER_REVIEW -> APPROVED |
| `reject(db, prompt, user, note?)` | `Session`, `Prompt`, `User`, `str?` | `Prompt` | UNDER_REVIEW -> CHANGES_REQUIRED |
| `publish(db, prompt, user, note?)` | `Session`, `Prompt`, `User`, `str?` | `Prompt` | APPROVED -> PUBLISHED, creates version snapshot |
| `deprecate(db, prompt, user, note?)` | `Session`, `Prompt`, `User`, `str?` | `Prompt` | PUBLISHED -> DEPRECATED |
| `retire(db, prompt, user, note?)` | `Session`, `Prompt`, `User`, `str?` | `Prompt` | DEPRECATED -> RETIRED |

### 3.7 `backend/app/services/audit_service.py` — Audit logging

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `record(db, event_type, user, entity_type?, entity_ref?, entity_name?, details?)` | `Session`, `str`, `User`, kwargs | None | Writes immutable audit event |

### 3.8 `backend/app/services/analytics_service.py` — Analytics

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `overview(db)` | `Session` | `dict` | Aggregate stats: counts, rates, time saved, trends |

---

## 4. Backend — quality engine

### 4.1 `backend/app/quality/engine.py` — Rubric scoring

**Rubric (100 points total):**

| Component | Max | Scoring method |
|-----------|-----|----------------|
| Goal | 20 | 20 if goal text contains a valid verb from GOAL_VERBS, else 0 |
| Context | 15 | min(15, 8 + markers_found * 4) if context present, else 0 |
| Source | 15 | min(15, 8 + markers_found * 4) if source present, else 0 |
| Expectations | 20 | min(20, 8 + markers_found * 4) if expectations present, else 0 |
| Specificity | 10 | 4 if text >= 80 chars + 3 if specificity markers + 3 if length hints |
| Constraints | 5 | 5 if constraint markers or text present, else 0 |
| Audience | 5 | 5 if audience text present, else 0 |
| Output format | 5 | 5 if output_format text present, else 0 |
| Examples | 5 | 5 if examples text present, else 0 |

**Rating bands:** >= 90 Excellent, >= 75 Good, >= 60 Needs improvement, < 60 Poor

**Key functions:**

| Function | Input | Output |
|----------|-------|--------|
| `classify(raw_text)` | `str` | `PromptAnalysis` |
| `analyse_prompt_fields(goal, context, source, expectations, audience, output_format, examples?, constraints?)` | field strings | `PromptAnalysis` |
| `rating_for(score)` | `int` | `str` |

### 4.2 `backend/app/quality/assistant.py` — Prompt generation/improvement

| Function | Input | Output |
|----------|-------|--------|
| `build_improved_prompt(raw, analysis)` | `str`, `PromptAnalysis` | `str` (improved prompt) |
| `generate_prompt(business_function, task, intent)` | `str`, `str`, `str` | `str` (generated prompt) |
| `explain(raw, analysis)` | `str`, `PromptAnalysis` | `str` (plain-English explanation) |

---

## 5. Backend — LLM layer

### 5.1 `backend/app/llm/base.py` — Abstract provider

**LLMProvider interface:**

| Method | Input | Output |
|--------|-------|--------|
| `generate(prompt_text, system?, temperature?, grounding?, task_hint?, output_format_hint?, max_tokens?)` | `str`, kwargs | `GenerationResult` |
| `list_models()` | — | `list[dict]` |
| `available` (property) | — | `bool` |

**GenerationResult dataclass:** `output`, `model`, `provider`, `tokens`, `latency_ms`, `finish_reason`, `metadata`

**GroundingContext dataclass:** `chunks` (list of dicts), `sources` (list of strings), `evidence` (list of dicts)

### 5.2 `backend/app/llm/mock.py` — Mock provider

**Input:** prompt text (task type inferred from content)
**Output:** deterministic text based on task type, with heuristic eval metrics

### 5.3 `backend/app/llm/providers.py` — Real providers

| Provider | Constructor input | API called |
|----------|------------------|------------|
| `OllamaProvider` | `base_url`, `model_name` | `POST /api/generate` |
| `OpenAIProvider` | `base_url`, `model`, `api_key` | `POST /v1/chat/completions` |
| `LiteLLMProvider` | `base_url`, `model`, `api_key` | `POST /v1/chat/completions` |

### 5.4 `backend/app/llm/factory.py` — Provider selection

| Function | Input | Output |
|----------|-------|--------|
| `get_provider(choice?)` | `str?` | `LLMProvider` |
| `discover_models()` | — | `list[dict]` |
| `provider_options()` | — | `list[dict]` |

---

## 6. Backend — RAG retriever

### 6.1 `backend/app/rag/retriever.py` — Local keyword retrieval

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `LocalRetriever(db).retrieve(query, doc_ids?, top_k?)` | `str`, `list[int]?`, `int?` | `GroundingContext` | TF keyword matching over document chunks |

**Scoring:** Tokenise query, count term frequency in each chunk, rank by overlap ratio, return top_k chunks with source names and snippets.

---

## 7. Backend — seed data

### 7.1 `backend/app/seed/__init__.py` — Seed orchestrator

| Function | Input | Output |
|----------|-------|--------|
| `seed_all()` | — | None (writes to DB) |

**Seeds:** 8 users, 68 prompts, 5 policies, 16 documents, 5 workflows, analytics rows, knowledge source links. Skips if `henry` user already exists.

### 7.2 `backend/app/seed/users_catalog.py` — User definitions

**Output:** `USERS: list[dict]` — 8 users with username, display_name, email, department, title, role. All share password `password`.

### 7.3 `backend/app/seed/prompts_catalog.py` — Prompt definitions

**Output:** `PROMPTS: list[dict]` — 68 prompts with name, description, business_function, application, task, goal, context, source, expectations, template, inputs, tags, risk_level, data_classification, etc.

### 7.4 `backend/app/seed/workflows_catalog.py` — Workflow definitions

**Output:** `WORKFLOWS: list[dict]` — 5 workflows with name, description, steps (each with prompt_name and input_mapping).

### 7.5 `backend/app/seed/governance_catalog.py` — Policy definitions

**Output:** `POLICIES: list[dict]` — 5 policies with name, description, condition (field/operator/value), action (type/label/value), severity.

### 7.6 `backend/app/seed/synthetic_m365.py` — Document generator

| Function | Input | Output |
|----------|-------|--------|
| `build_all()` | — | `list[dict]` (16 documents with name, doc_type, content, metadata) |

---

## 8. Backend — models (ORM entities)

### `backend/app/models/entities.py`

| Model | Table | Key columns |
|-------|-------|-------------|
| `User` | `users` | id, user_id (USER-0001), username, display_name, email, department, title, role, password_hash |
| `Prompt` | `prompts` | id, prompt_id (PROMPT-000001), name, description, status, version, version_number, owner_id, business_function, application, task, goal, context, source, expectations, system_instruction, prompt_template, audience, tone, output_format, max_length, data_classification, risk_level, requires_approval, contains_pii, contains_financial_data, contains_customer_data, external_sharing, temperature, quality_score, tags, is_system, published_at |
| `PromptInput` | `prompt_inputs` | id, prompt_id, name, input_type, required, description, sample_value, position |
| `PromptVersion` | `prompt_versions` | id, prompt_id, version, author_id, changes, snapshot (JSON) |
| `PromptExecution` | `prompt_executions` | id, execution_id (EXEC-...), prompt_id, version, user_id, provider, model, temperature, input_data, output, status, tokens, latency_ms, sources_used, evidence, eval_metrics, error_message, estimated_time_saved_minutes |
| `PromptRating` | `prompt_ratings` | id, prompt_id, user_id, stars, useful |
| `PromptFavourite` | `prompt_favourites` | id, prompt_id, user_id |
| `Workflow` | `workflows` | id, workflow_id (WORKFLOW-...), name, description, status, owner_id, business_function, tags, estimated_manual_minutes, estimated_ai_minutes |
| `WorkflowStep` | `workflow_steps` | id, step_id (STEP-001), workflow_id, sequence, name, prompt_id, input_mapping, continue_on_failure |
| `WorkflowExecution` | `workflow_executions` | id, execution_id (WRUN-...), workflow_id, status, inputs, step_results, final_output, sources_used, latency_ms, error_message |
| `GovernancePolicy` | `governance_policies` | id, policy_id (POLICY-...), name, description, condition (JSON), action (JSON), severity, enabled |
| `ComplianceViolation` | `compliance_violations` | id, violation_id (VIO-...), policy_id, message, severity |
| `ApprovalRequest` | `approval_requests` | id, approval_id (APPROVAL-...), prompt_id, requester_id, reviewer_id, status, decision, notes |
| `Document` | `documents` | id, doc_id (DOC-...), name, doc_type, source_app, department, author, summary, content, metadata_, synthetic |
| `DocumentChunk` | `document_chunks` | id, document_id, chunk_index, content, char_start, char_end |
| `KnowledgeSource` | `knowledge_sources` | id, prompt_id, document_id, source_type |
| `AuditEvent` | `audit_events` | id, event_id (EVT-...), event_type, actor, entity_type, entity_ref, entity_name, details (JSON) |
| `SQLiteSequence` | `sqlite_sequences` | counter_type, next_value |

---

## 9. Backend — schemas (Pydantic)

### `backend/app/schemas/api.py`

**Request schemas:**

| Schema | Fields | Used by |
|--------|--------|---------|
| `LoginRequest` | `username`, `password` | POST /auth/login |
| `PromptCreate` | `name`, `description`, `business_function`, `application`, `task`, `goal`, `context`, `source`, `expectations`, `system_instruction`, `prompt_template`, `audience`, `tone`, `output_format`, `max_length`, `data_classification`, `risk_level`, `requires_approval`, `contains_pii`, `contains_financial_data`, `contains_customer_data`, `external_sharing`, `temperature`, `require_evidence`, `avoid_unsupported_claims`, `ask_clarification_questions`, `manual_time_minutes`, `ai_time_minutes`, `tags`, `inputs`, `knowledge_source_document_ids` | POST /prompts |
| `PromptUpdate` | Same as PromptCreate but all optional | PUT /prompts/{ref} |
| `PromptFlowAction` | `action` (str), `note?` (str) | POST /prompts/{ref}/flow |
| `RatingCreate` | `stars` (float), `useful?` (str) | POST /prompts/{ref}/rate |
| `CloneCreate` | `name?` (str) | POST /prompts/{ref}/clone |
| `AssistantRequest` | `prompt` (str), `mode?` (str), `business_function?`, `task?` | POST /assistant/* |
| `ExecutionRequest` | `prompt_id` (int), `input_data?` (dict), `model_provider?`, `model_name?`, `temperature?`, `document_ids?` (list), `use_grounding?` (bool) | POST /executions |
| `WorkflowCreate` | `name`, `description?`, `business_function?`, `tags?`, `steps?` (list of `WorkflowStepIn`) | POST /workflows |
| `WorkflowStepIn` | `sequence`, `name?`, `prompt_id`, `input_mapping?`, `continue_on_failure?` | nested in WorkflowCreate |
| `WorkflowRunRequest` | `input_data?` (dict), `document_ids?` (list) | POST /workflows/{ref}/run |
| `GovernanceEvaluationIn` | `data_classification`, `risk_level`, `contains_pii`, `contains_financial_data`, `contains_customer_data`, `external_sharing`, `llm_provider` | POST /governance/evaluate |
| `PolicyIn` | `name`, `description?`, `condition?`, `action?`, `severity`, `enabled` | POST /governance/policies |

**Response schemas:**

| Schema | Key fields |
|--------|-----------|
| `LoginResponse` | `token`, `user` (UserSummary) |
| `PromptListResponse` | `items` (PromptSummary[]), `total`, `page`, `page_size` |
| `PromptDetail` | All prompt fields + `inputs`, `versions`, `quality_score`, `governance`, `is_favourite`, `execution_count`, `rating_avg` |
| `PromptSummary` | `id`, `prompt_id`, `name`, `description`, `status`, `version`, `business_function`, `application`, `task`, `quality_score`, `risk_level`, `data_classification`, `tags`, `execution_count`, `rating_avg`, `updated_at` |
| `AssistantResponse` | `score`, `rating`, `breakdown`, `missing`, `present`, `recommendations`, `analysis`, `improved_prompt`, `generated_prompt`, `explanation` |
| `ExecutionOut` | `id`, `execution_id`, `prompt_id`, `provider`, `model`, `status`, `output`, `tokens`, `latency_ms`, `sources_used`, `evidence`, `eval_metrics`, `estimated_time_saved_minutes` |
| `WorkflowOut` | `id`, `workflow_id`, `name`, `description`, `status`, `steps`, `estimated_manual_minutes`, `estimated_ai_minutes` |
| `WorkflowExecutionOut` | `id`, `execution_id`, `workflow_name`, `status`, `step_results`, `final_output`, `latency_ms` |
| `GovernanceEvaluationOut` | `approved`, `violations`, `decisions` |
| `PolicyOut` | `id`, `policy_id`, `name`, `description`, `condition`, `action`, `severity`, `enabled` |
| `AnalyticsOverview` | `prompt_count`, `published_count`, `execution_count`, `success_rate`, `avg_rating`, `estimated_time_saved_minutes`, `top_prompts`, `execution_by_category`, etc. |
| `VersionOut` | `version`, `author`, `changes`, `created_at` |
| `VersionDetail` | `version`, `author`, `changes`, `snapshot`, `created_at` |
| `VersionCompare` | `from_version`, `to_version`, `changes` |

---

## 10. Backend — enums and constants

The `core/enums.py` module exports catalogue lists used by:

- **Backend:** prompt_service (filter options), governance (condition matching)
- **Frontend:** Catalog API -> dropdown options in Library, Builder, Governance

---

## 11. Frontend — application core

### 11.1 `frontend/src/main.tsx` — Bootstrap

**Purpose:** Mounts the React app with BrowserRouter and QueryClientProvider.
**Inputs:** HTML element `#root`
**Outputs:** Renders `<App />` inside providers

### 11.2 `frontend/src/App.tsx` — Routing

| Path | Component | Description |
|------|-----------|-------------|
| `/` | `Dashboard` | Overview stats and charts |
| `/library` | `Library` | Browse/search/filter prompts |
| `/prompts/:id` | `PromptDetail` | Single prompt detail + execute |
| `/builder` | `Builder` | Create new prompt |
| `/builder/:id` | `Builder` | Edit existing prompt |
| `/assistant` | `Assistant` | Quality analysis tool |
| `/workflows` | `Workflows` | List + run workflows |
| `/analytics` | `AnalyticsPage` | Charts and metrics |
| `/governance` | `Governance` | Policies, evaluation, violations |
| `/audit` | `Audit` | Audit event log |
| `/admin` | `Admin` | User management |
| `*` | `Navigate -> /` | Catch-all redirect |

---

## 12. Frontend — API client

### 12.1 `frontend/src/api/client.ts` — HTTP wrapper

| Export | Input | Output |
|--------|-------|--------|
| `api.get<T>(path)` | `string` | `Promise<T>` |
| `api.post<T>(path, body?)` | `string`, `unknown?` | `Promise<T>` |
| `api.put<T>(path, body)` | `string`, `unknown` | `Promise<T>` |
| `api.del<T>(path)` | `string` | `Promise<T>` |

**Base URL:** `VITE_API_URL` env var or `"/api/v1"` (proxied by Vite in dev)

### 12.2 `frontend/src/api/index.ts` — Domain API functions

| Export | Backend endpoint | Input | Output |
|--------|-----------------|-------|--------|
| `catalogApi.get()` | `GET /catalog` | — | `Catalog` |
| `promptsApi.list(params?)` | `GET /prompts` | filter params | `PromptListResponse` |
| `promptsApi.get(ref)` | `GET /prompts/{ref}` | `string` | `PromptDetail` |
| `promptsApi.create(data)` | `POST /prompts` | `PromptCreatePayload` | `PromptDetail` |
| `promptsApi.update(ref, data)` | `PUT /prompts/{ref}` | `string`, payload | `PromptDetail` |
| `promptsApi.delete(ref)` | `DELETE /prompts/{ref}` | `string` | `void` |
| `promptsApi.clone(ref, data?)` | `POST /prompts/{ref}/clone` | `string`, payload? | `PromptDetail` |
| `promptsApi.flow(ref, data)` | `POST /prompts/{ref}/flow` | `string`, `PromptFlowAction` | `PromptDetail` |
| `promptsApi.rate(ref, data)` | `POST /prompts/{ref}/rate` | `string`, `RatingCreate` | `RatingOut` |
| `promptsApi.favourite(ref)` | `POST /prompts/{ref}/favourite` | `string` | `boolean` |
| `promptsApi.governance(ref)` | `GET /prompts/{ref}/governance` | `string` | governance result |
| `promptsApi.versions(ref)` | `GET /prompts/{ref}/versions` | `string` | `VersionOut[]` |
| `promptsApi.compare(ref, from, to)` | `GET /prompts/{ref}/compare` | 3 strings | `VersionCompare` |
| `assistantApi.analyse(data)` | `POST /assistant/analyse` | `AssistantRequest` | `AssistantResponse` |
| `assistantApi.improve(data)` | `POST /assistant/improve` | `AssistantRequest` | `AssistantResponse` |
| `assistantApi.generate(data)` | `POST /assistant/generate` | `AssistantRequest` | `AssistantResponse` |
| `assistantApi.explain(data)` | `POST /assistant/explain` | `AssistantRequest` | `AssistantResponse` |
| `executionsApi.create(data)` | `POST /executions` | `ExecutionRequest` | `ExecutionOut` |
| `executionsApi.list(params?)` | `GET /executions` | filter params | `ExecutionListResponse` |
| `workflowsApi.list()` | `GET /workflows` | — | `WorkflowListResponse` |
| `workflowsApi.get(ref)` | `GET /workflows/{ref}` | `string` | `WorkflowOut` |
| `workflowsApi.run(ref, data)` | `POST /workflows/{ref}/run` | `string`, `WorkflowRunRequest` | `WorkflowExecutionOut` |
| `governanceApi.policies()` | `GET /governance/policies` | — | `PolicyOut[]` |
| `governanceApi.evaluate(data)` | `POST /governance/evaluate` | evaluation payload | evaluation result |
| `governanceApi.scan(text)` | `POST /governance/scan` | `string` | scan result |
| `governanceApi.summary()` | `GET /governance/summary` | — | summary dict |
| `analyticsApi.overview()` | `GET /analytics/overview` | — | `AnalyticsOverview` |
| `auditApi.list(params?)` | `GET /audit` | filter params | `AuditListResponse` |
| `adminApi.users()` | `GET /admin/users` | — | `UserSummary[]` |
| `knowledgeApi.documents(params?)` | `GET /knowledge/documents` | page params | document list |

### 12.3 `frontend/src/api/types.ts` — TypeScript types

**Purpose:** Mirrors every backend Pydantic schema as a TypeScript type.

**Key types:** `PromptSummary`, `PromptDetail`, `PromptCreatePayload`, `PromptFlowAction`, `RatingCreate`, `AssistantRequest`, `AssistantResponse`, `ExecutionOut`, `ExecutionRequest`, `WorkflowOut`, `WorkflowExecutionOut`, `WorkflowRunRequest`, `GovernanceEvaluationIn`, `GovernanceEvaluationOut`, `PolicyIn`, `PolicyOut`, `Catalog`, `AnalyticsOverview`, `AuditEventOut`, `VersionOut`, `VersionDetail`, `VersionCompare`, `UserSummary`, `PromptInputOut`, `PromptInputIn`

---

## 13. Frontend — shared UI components

### `frontend/src/components/ui.tsx`

| Component | Props | Description |
|-----------|-------|-------------|
| `Button` | `children`, `variant?` ("primary"/"secondary"/"ghost"/"danger"), `className?`, HTML button attrs | Styled button |
| `Card` | `title?`, `children`, `action?` | White card with optional header |
| `Badge` | `color?` ("blue"/"purple"/"green"/"amber"/"red"/"slate"), `children` | Coloured pill badge |
| `QualityRing` | `score` (0-100), `size?` (px) | SVG circular progress ring |
| `StatusBadge` | `status` (string) | Badge coloured by status |
| `Spinner` | `label?` | Loading spinner with optional text |
| `Empty` | `message` | Empty state placeholder |
| `StatCard` | `label`, `value`, `sub?` | Dashboard stat card |

### `frontend/src/components/Layout.tsx`

**Purpose:** App shell with sidebar navigation and top bar.
**Props:** None (wraps `<Outlet />`)
**Renders:** Sidebar with nav links (Dashboard, Library, Builder, Assistant, Workflows, Analytics, Governance, Audit, Admin) + governance high-risk badge.

---

## 14. Frontend pages

### `frontend/src/pages/Dashboard.tsx`

**API calls:** `analyticsApi.overview()`, `executionsApi.list({limit: 5})`
**Renders:** Stat cards (prompts, executions, success rate, time saved, avg rating), execution trend line chart, top prompts bar chart, category pie chart, recent executions table.

### `frontend/src/pages/Library.tsx`

**API calls:** `promptsApi.list(filters)`, `catalogApi.get()`
**State:** URL search params (page, search, business_function, task, status, risk_level, sort)
**Renders:** Search bar, filter dropdowns, prompt card grid, pagination.

### `frontend/src/pages/PromptDetail.tsx`

**API calls:** `promptsApi.get(ref)`, `executionsApi.create(data)`, `promptsApi.flow(ref, data)`, `promptsApi.governance(ref)`, `promptsApi.versions(ref)`, `promptsApi.compare(ref, from, to)`
**Renders:** Prompt info, quality ring, four-part framework, inputs form, execution panel, lifecycle buttons, governance check, version history.

### `frontend/src/pages/Builder.tsx`

**API calls:** `catalogApi.get()`, `promptsApi.create(data)`, `promptsApi.update(ref, data)`
**Renders:** Multi-section form (name, framework fields, inputs, governance attributes, tags). Submit creates or updates prompt.

### `frontend/src/pages/Assistant.tsx`

**API calls:** `assistantApi.analyse/improve/generate/explain(data)`
**Renders:** Mode selector, text input, quality breakdown, recommendations, improved/generated/explained output.

### `frontend/src/pages/Workflows.tsx`

**API calls:** `workflowsApi.list()`, `workflowsApi.run(ref, data)`
**State:** `configuring` (selected workflow), `inputValues` (form data)
**Renders:** Workflow cards, input form (auto-extracted from step mappings), run results with step-by-step status.

### `frontend/src/pages/Analytics.tsx`

**API calls:** `analyticsApi.overview()`
**Renders:** Stat cards, line chart (daily trend), bar chart (top prompts), pie chart (categories), model usage, status distribution.

### `frontend/src/pages/Governance.tsx`

**API calls:** `governanceApi.summary()`, `governanceApi.policies()`, `governanceApi.evaluate(data)`, `governanceApi.scan(text)`
**Renders:** Summary stat cards, risk distribution, violations list, evaluation sandbox form, active policies, security scanner.

### `frontend/src/pages/Audit.tsx`

**API calls:** `auditApi.list({event_type, actor, limit, offset})`
**Renders:** Filterable audit event table with pagination.

### `frontend/src/pages/Admin.tsx`

**API calls:** `adminApi.users()`
**Renders:** User table with username, role, department, email.

---

## 15. Infrastructure files

### `frontend/package.json`

**Dependencies:** react 18, react-dom 18, react-router-dom 6, @tanstack/react-query 5, recharts 2, clsx 2
**Dev dependencies:** typescript 5, vite 5, @vitejs/plugin-react 4, tailwindcss 3, postcss 8, autoprefixer 10

### `frontend/vite.config.ts`

**Purpose:** Vite build config with React plugin and dev proxy (`/api` -> `127.0.0.1:8000`).
**Env var:** `VITE_PROXY_TARGET` overrides the proxy target.

### `frontend/tailwind.config.js`

**Purpose:** Tailwind CSS config with brand colour palette and content paths.

### `frontend/src/lib/format.ts`

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `formatTime(value)` | `string \| null` | `string` | ISO timestamp to locale string |
| `formatDate(value)` | `string \| null` | `string` | ISO timestamp to locale date |
| `stripMarkdown(value, max?)` | `string \| null`, `number` | `string` | Removes markdown syntax, truncates |
| `truncate(value, max?)` | `string`, `number` | `string` | Truncates with ellipsis |

### `docker-compose.yml`

**Services:** postgres, qdrant, ollama, backend (uvicorn), frontend (nginx)
**Backend Dockerfile:** `backend/Dockerfile` — Python 3.14, uv sync, seeds then runs uvicorn
**Frontend Dockerfile:** `frontend/Dockerfile` — Node 20, npm build, nginx serve, bakes `VITE_API_URL`

### `backend/Dockerfile`

**Base:** Python 3.14-slim
**Build:** `uv sync --frozen`
**Run:** seeds, then `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### `frontend/Dockerfile`

**Base:** Node 20-alpine
**Build:** `npm install && npm run build`
**Serve:** nginx:alpine on port 80
**Env baked in:** `VITE_API_URL=http://localhost:8000/api/v1`

### `backend/tests/conftest.py`

**Purpose:** pytest fixtures — temp SQLite DB, test client, seeded test data.
**Key fixtures:** `db_session`, `client`, `seeded_db`

### `backend/tests/test_quality_engine.py`

**Purpose:** 12 tests for the quality rubric — scoring, rating bands, edge cases.

### `backend/tests/test_api.py`

**Purpose:** 11 tests for API integration — CRUD, lifecycle, execution, governance, analytics.

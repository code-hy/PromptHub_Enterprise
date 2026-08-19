# PromptHub Enterprise — Technical Guide

This guide explains the technology stack, the responsibility of every component,
and how the pieces fit together in the overall system. It is written for
engineers who will operate, extend or migrate the platform.

---

## Table of contents

- [1. System design at a glance](#1-system-design-at-a-glance)
- [2. Technology stack](#2-technology-stack)
- [3. Configuration layer](#3-configuration-layer)
- [4. Backend application layer](#4-backend-application-layer)
- [5. Data layer](#5-data-layer)
- [6. LLM abstraction (provider gateway)](#6-llm-abstraction-provider-gateway)
- [7. RAG / knowledge grounding](#7-rag--knowledge-grounding)
- [8. Deterministic quality engine](#8-deterministic-quality-engine)
- [9. Execution pipeline](#9-execution-pipeline)
- [10. Workflow engine](#10-workflow-engine)
- [11. Governance engine](#11-governance-engine)
- [12. Audit trail](#12-audit-trail)
- [13. Seeding architecture](#13-seeding-architecture)
- [14. Frontend architecture](#14-frontend-architecture)
- [15. Authentication & authorization](#15-authentication--authorization)
- [16. Testing strategy](#16-testing-strategy)
- [17. Build, deploy & operations](#17-build-deploy--operations)
- [18. Data-flow walkthroughs](#18-data-flow-walkthroughs)
- [19. Extending the platform](#19-extending-the-platform)

---

## 1. System design at a glance

```
                  ┌──────────────────────────────────────────────────┐
                  │                    BROWSER                        │
                  │      React 18 SPA (Vite dev or static build)      │
                  └──────────────────────┬───────────────────────────┘
                                         │ HTTP/JSON  (proxied in dev,
                                         │            direct + CORS in prod)
                  ┌──────────────────────▼───────────────────────────┐
                  │                FASTAPI (:8000)                    │
                  │  Catalog │ Prompts │ Assistant │ Executions       │
                  │  Workflows │ Governance │ Analytics │ Audit       │
                  │  Admin │ Knowledge                     /api/v1    │
                  ├───────────────────────────────────────────────────┤
                  │  SERVICES  (business logic, orchestration)        │
                  ├───────────────────────────────────────────────────┤
                  │  LLM  Quality  RAG      Governance    Audit       │
                  │  gate engine  retriev  policy engine  writer      │
                  ├───────────────────────────────────────────────────┤
                  │  SQLAlchemy ORM  →  SQLite (dev) / PostgreSQL     │
                  └──────────────┬────────────────────────────────────┘
                                 │
   (optional external)  ┌────────△───────┐
                        │Qdrant │ Ollama  │ OpenAI-compatible
                        └───────┴─────────┘
```

Design principles:

1. **Vendor-neutral LLM access** — the app never talks to a model directly; it
   depends on the `LLMProvider` abstraction so mock / Ollama / OpenAI can be
   swapped by configuration.
2. **Deterministic core** — quality scoring, security scanning and output
   evaluation are rule-based (no LLM), which makes scores stable, explainable
   and unit-testable.
3. **Zero-dependency demo** — SQLite + mock provider means the entire platform
   boots with nothing else installed; PostgreSQL/Qdrant/Ollama are opt-in.
4. **Every mutation is auditable** — mutation services write an `audit_events`
   row as part of the same transaction.

---

## 2. Technology stack

### Backend

| Technology | Version | Role |
|------------|---------|------|
| Python | >= 3.11 | Runtime |
| FastAPI | >= 0.115 | Web framework, routing, OpenAPI generation |
| Uvicorn | >= 0.30 (standard) | ASGI server |
| Pydantic | >= 2.7 | Request/response schemas, validation |
| SQLAlchemy | >= 2.0 | ORM, session management, DDL |
| Pydantic-Settings | >= 2.4 | `.env` / env-var configuration |
| psycopg (binary) | >= 3.2 | PostgreSQL driver |
| httpx | >= 0.27 | Outbound calls (Ollama/LiteLLM health + completions) |
| numpy | >= 1.26 | (optional) numeric work in analytics/heuristics |
| python-multipart | >= 0.0.9 | Form parsing support |

Dev/test: `pytest`, `pytest-asyncio`, `ruff`.

### Frontend

| Technology | Version | Role |
|------------|---------|------|
| React | 18 | UI library |
| TypeScript | 5.x | Typed client and components |
| Vite | 5.x | Bundler + dev server with `/api` proxy |
| Tailwind CSS | 3.x | Styling (custom `brand` palette) |
| TanStack React Query | 5.x | Server-state caching, mutations, invalidation |
| React Router | 6.x | Routing (client-side) |
| Recharts | 2.x | Analytics charts |

### Infrastructure (optional)

| Technology | Role in the system |
|------------|--------------------|
| PostgreSQL 16 | Production-grade relational store (replaces SQLite via `DATABASE_URL`) |
| Qdrant | Vector store for embeddings-based retrieval (`RAG_MODE=qdrant`) |
| Ollama | Local LLM inference (`LLM_PROVIDER=ollama` or `auto`) |
| Docker Compose | Bundles the whole stack (postgres, qdrant, ollama, backend, frontend) |

---

## 3. Configuration layer

**File:** `backend/app/config.py`

`Settings` is a `pydantic-settings.BaseSettings` subclass. Precedence:

```
environment variables  >  .env file  >  hard-coded defaults
```

The `.env` file is loaded from the **repository root** (the parent of
`backend/`):

```python
BASE_DIR = Path(__file__).resolve().parent.parent.parent
model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), ...)
```

Notable properties:

| Setting | Default | Purpose |
|---------|---------|---------|
| `api_prefix` | `/api/v1` | Mounted by every router in `main.py` |
| `database_url` | `""` | `""` → SQLite; `postgresql+psycopg://…` → PostgreSQL |
| `llm_provider` | `auto` | Provider selection (see §6) |
| `ollama_base_url` / `ollama_model` | localhost:11434 / `qwen3:1.7b` | Ollama gateway |
| `openai_api_key` / `openai_base_url` / `openai_model` | empty / api.openai.com / `gpt-4o-mini` | OpenAI gateway |
| `rag_mode` | `local` | Retrieval backend selection |
| `cors_origins` | localhost:5173/:4173 (+127.0.0.1) | CORS allow-list |
| `enable_auth` | `false` | Auth off → auto demo user |
| `secret_key` | dev default | HMAC token signing |
| `seed_demo_data` | `true` | Seed on startup |

`settings.sqlalchemy_url` (derived) collapses `database_url` to a concrete
SQLAlchemy URL and is consumed by the database layer — so switching storage is a
single env var change.

---

## 4. Backend application layer

### Entrypoint — `backend/app/main.py`

```python
@asynccontextmanager
async def lifespan(app):
    init_db()          # create_all on the SQLAlchemy metadata
    if settings.seed_demo_data:
        seed_all()     # no-op if the DB is already seeded
    yield

for router in (catalog, auth, prompts, assistant, executions,
               workflows, governance, analytics, audit, admin, knowledge):
    app.include_router(router, prefix=settings.api_prefix)
```

`init_db()` (in `database.py`) imports `app.models` (registering classes on the
declarative `Base.metadata`) and runs `Base.metadata.create_all`. There is no
Alembic migration in the current runtime path — **the model file is the DDL
contract** (see §5).

### Router layer — `backend/app/api/`

One router per domain, thin: parse/serialize via Pydantic, delegate to a service.

| Router | Responsibilities |
|--------|------------------|
| `catalog.py` | Free-form dropdown values (functions, tasks, apps, statuses, risk, tones…), model/provider lists |
| `prompts.py` | CRUD, clone, lifecycle `flow`, rating, favourite, per-prompt governance, versions, compare |
| `assistant.py` | `analyse` / `improve` / `generate` / `explain` (all hit `assistant_service.analyse`) |
| `executions.py` | Run a prompt, list/get executions |
| `workflows.py` | CRUD + run + executions history |
| `governance.py` | Policy CRUD, `evaluate`, `scan`, `violations`, `summary` |
| `analytics.py` | `overview`, `productivity` |
| `audit.py` | Paginated audit log, `recent` |
| `knowledge.py` | Document browsing and RAG `search` |
| `admin.py` | User directory (ADMIN role) |
| `auth.py` | `login`, `me` |

### Service layer — `backend/app/services/`

Holds business logic and transaction boundaries:

| Service | Key functions |
|---------|---------------|
| `prompt_service` | `list_prompts` (SQL + counts + sorting), `create_prompt` (computes quality on save), `update_prompt` (auto-versions published prompts), `clone_prompt`, `rate_prompt`, `list_versions`, `get/compare` |
| `execution_service` | `run_prompt` (§9), `evaluate_output` (deterministic eval metrics) |
| `workflow_service` | `run_workflow` (§10), CRUD, input mapping resolution |
| `governance_service` | Policy engine, security scanner, summary (§11) |
| `analytics_service` | Aggregation queries over executions/ratings |
| `audit_service` | `record(...)` event writer (§12) |
| `assistant_service` | Thin wrapper over the quality engine for the 4 modes |
| `lifecycle_service` | State-machine transitions with audit + version capture |

---

## 5. Data layer

### Engine & sessions — `backend/app/database.py`

```python
engine = create_engine(settings.sqlalchemy_url, **kwargs)   # sqlite: check_same_thread=False
# sqlite only: PRAGMA foreign_keys=ON on connect
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
get_db() -> Generator[Session]   # FastAPI dependency, always closes
```

`pool_pre_ping` is enabled for PostgreSQL to avoid stale-connection errors.

### Models — `backend/app/models/entities.py`

`Prompt.quality_score`, `AuditEvent.event_id`, `WorkflowExecution.workflow_name`,
`PromptVersion.version_number` and the `SQLiteSequence` counter table were added
during the initial implementation to satisfy unique constraints and analytics.

Tables (declarative `Base`):

| Table | Entity | Purpose |
|-------|--------|---------|
| `users` | `User` | Auth, ownership, roles |
| `prompts` | `Prompt` | Prompt record + all structured attributes + `quality_score` |
| `prompt_versions` | `PromptVersion` | Immutable version snapshots (`snapshot` JSON) |
| `prompt_inputs` | `PromptInput` | Declared `{placeholder}` inputs with type/required/description |
| `prompt_ratings` / `prompt_favourites` / `prompt_shares` / `prompt_reviews` | | Engagement + approval records |
| `documents` / `document_chunks` | `Document`, `DocumentChunk` | Synthetic Contoso corpus + 400-char chunks |
| `knowledge_sources` | `KnowledgeSource` | Prompt↔document links |
| `prompt_executions` | `PromptExecution` | One row per run (output, metrics, sources, latency) |
| `workflows` / `workflow_steps` | `Workflow`, `WorkflowStep` | Promptbook + ordered steps with input mappings |
| `workflow_executions` | `WorkflowExecution` | One row per workflow run (`step_results` JSON) |
| `governance_policies` | `GovernancePolicy` | IF {condition} THEN {action} rules |
| `approval_requests` | `ApprovalRequest` | Pending review gate |
| `compliance_violations` | `ComplianceViolation` | Raised by the policy engine |
| `audit_events` | `AuditEvent` | Immutable event log |
| `seq_counters` | `SQLiteSequence` | Business-formatted ID counters |

### Business identifiers — `backend/app/ids.py`

All human-facing IDs use a counter table (`seq_counters`), producing readable
keys like `PROMPT-000123`, `EXEC-00000042`, `WORKFLOW-000001`, `WRUN-00000007`,
`POLICY-00005`, `EVT-00000001`, `DOC-000001`, `USER-0001`, `VIO-000001`. This
decouples IDs from database row numbers and works identically on SQLite and
PostgreSQL. The seed advances the prompt counter past the seeded set so
runtime-created prompts never collide.

---

## 6. LLM abstraction (provider gateway)

**Files:** `app/llm/base.py`, `app/llm/providers.py`, `app/llm/mock.py`,
`app/llm/factory.py`, `app/llm/__init__.py`

The abstraction that makes the whole system vendor-neutral:

```python
class LLMProvider(abc.ABC):
    def generate(self, prompt_text, *, system, temperature,
                 grounding: GroundingContext | None, task_hint,
                 output_format_hint, max_tokens) -> GenerationResult: ...

class GenerationResult:
    output: str; model: str; provider: str; tokens: int
    latency_ms: int; finish_reason: str; metadata: dict

class GroundingContext:
    chunks: list[dict]      # {name, snippet, source, document_id}
    sources: list[str]
    evidence: list[dict]
```

**Concrete providers:**

| Provider | Notes |
|----------|-------|
| `MockProvider` | Deterministic template-based output, configurable `latency_ms`. Used by tests (`MOCK_LLM_LATENCY_MS=0`) and offline demos. Same input ⇒ same output |
| `OllamaProvider` | `/api/chat` via httpx; `list_models()` pulls `/api/tags` |
| `OpenAIProvider` | OpenAI-compatible completions via httpx |
| `LiteLLMProvider` | Gateway wrapper (base-url + model) |

**Factory — `factory.py`:**

```python
get_provider("auto"):
    if _ollama_reachable(settings.ollama_base_url):  # GET /api/tags, 2s timeout
        return OllamaProvider(...)
    return MockProvider(...)
```

`discover_models()` dedupes the active provider's model list into
`[{name, provider, size, local}]` — surfaced through `/catalog` so the frontend
can populate model/provided dropdowns.

> **Why this matters in the scheme of things:** every execution path
> (single-prompt, workflow step) passes through this gateway. Adding a vendor
> means adding one provider class — no call-site changes.

---

## 7. RAG / knowledge grounding

**Files:** `app/rag/retriever.py`, seeded in `app/seed/synthetic_m365.py`.

The RAG layer grounds LLM output on the **synthetic Contoso M365 corpus** — 16
documents (Outlook/Teams/Word/Excel/PowerPoint) stored in `documents`, split into
**400-character chunks** in `document_chunks` at seed time.

`LocalRetriever` (default `RAG_MODE=local`) performs **plain TF-based keyword
matching**:

```python
_tokens():        re.findall(r"[a-z0-9]{3,}", text.lower())
_score_chunk():   overlap(query_tokens, chunk_tokens) / len(query_tokens)
```

So a chunk scores 100% if it contains every query token; matching is fast and
needs no embedding model. Retrieval is scoped per execution to the ground query
(joined input values) and can be restricted by `document_ids`.

Producer of `GroundingContext`: `hits = retriever.retrieve(query, top_k=5)` then
`chunks`, `sources` (document names) and `evidence` (document id/name/snippet).

> **Qdrant path** (`RAG_MODE=qdrant`) is provided by the compose environment and
> would replace the `LocalRetriever` scoring with embedding-based ANN search; the
> `GroundingContext` contract is unchanged.

---

## 8. Deterministic quality engine

**File:** `app/quality/engine.py`

A purely rule-based scorer — no LLM involved — which keeps results stable across
runs and testable in CI. Rubric (total 100):

```
Goal            20   action verb present (GOAL_VERBS)
Context         15   context/background markers
Source          15   source/data markers
Expectations    20   output/structure/should/must markers
Specificity     10   length ≥ 60 words, numbers/specific terms, length hints
Constraints      5   "do not / avoid / limit" markers
Audience         5   executive/board/team/customer markers
Output format    5   table/bullet/json/summary markers
Examples         5   example/e.g./sample markers
```

Two entry points:

| Function | Input | Used by |
|----------|-------|---------|
| `classify(text)` | Free-text prompt | Assistant `analyse/improve/generate/explain`, security of arbitrary text |
| `analyse_prompt_fields(goal, context, source, expectations, …)` | Structured Builder fields | `create_prompt` / `update_prompt`, seed scoring |

Both return a `PromptAnalysis` dataclass: `score`, `rating`
(`Excellent ≥ 90 / Good ≥ 75 / Needs improvement ≥ 60 / Poor`), `breakdown`,
`present`, `missing`, `recommendations` and per-component `evidence`.

The **Assistant improvements** (`app/quality/assistant.py`) build on it:
`build_improved_prompt` strengthens a prompt with missing components,
`generate_prompt` drafts from intent + function/task, and `explain` describes why
a prompt reads the way it does.

**Where it plugs in:** `prompt_service.create_prompt` computes and persists
`quality_score`; seeded prompts carry deterministic scores (min 62 / max 84).

---

## 9. Execution pipeline

**File:** `app/services/execution_service.py`

Flow for `POST /api/v1/executions`:

```
1. get_provider(req.model_provider)            → LLMProvider
2. if req.use_grounding OR prompt.require_evidence:
     query = joined input values (or goal/name)
     hits  = LocalRetriever.retrieve(query, top_k=5, document_ids)
     build GroundingContext {chunks, sources, evidence}
3. prompt_text = _resolve_prompt_template(prompt, input_data)
     re.sub(r"\{\{\s*(\w+)\s*\}\}", repl, template)   # {{name}} → input value
4. result = provider.generate(prompt_text,
     system=prompt.system_instruction or goal,
     temperature, grounding, task_hint=prompt.task,
     output_format_hint=prompt.output_format)
5. eval_metrics = evaluate_output(result.output, prompt, grounding)
6. persist PromptExecution(status=SUCCESS, tokens, latency_ms,
     sources_used, evidence, eval_metrics)
7. audit_service.record("PROMPT_EXECUTED", ...)   # same transaction
```

### Output evaluation — `evaluate_output`

Deterministic heuristics (7 weighted metrics):

| Metric | Weight | Heuristic |
|--------|--------|-----------|
| `instruction_score` | 0.20 | Section markers (`##`, `**`) match `expectations` |
| `grounding_score` | 0.20 | Output cites retrieved source names / "evidence" |
| `completeness_score` | 0.20 | Word count + list/table structure |
| `consistency_score` | 0.15 | Conclusion signals ("summary", "findings"…) |
| `relevance_score` | 0.15 | Output contains keywords from the goal |
| `safety_score` | 0.05 | No refusal phrases ("as an ai, i…") |
| `format_score` | 0.05 | Matches requested output format |

`overall_score` → grade. Stored in `eval_metrics` JSON and returned as
`ExecutionOut` for the UI.

---

## 10. Workflow engine

**File:** `app/services/workflow_service.py`

A promptbook = ordered `WorkflowStep`s with `input_mapping` such as
`{"emails": "input.project_emails"}` and `{"document": "step_4.output"}`.

`run_workflow` is **synchronous**:

```
1. create WorkflowExecution(status=RUNNING, execution_id=WRUN-…)
2. for each step sorted by sequence:
     resolved = _resolve_input(mapping, input_data, step_results, defaults)
                 # "input.field"      → from the run payload
                 # "step_N.output"    → output of the Nth completed step
                 # otherwise          → defaults / payload key
     RAG retrieve over resolved inputs
     provider.generate(templated prompt + system + grounding)
     append step_result {status, output, model, provider, tokens,
                         latency_ms, sources, evidence}
     track final_output (last successful output)
     on exception: FAILED; break unless step.continue_on_failure
3. finalize: status SUCCESS|FAILED, latency_ms, unique sources,
   ended_at
4. audit "WORKFLOW_EXECUTED"
```

Because each step re-enters the same `LLMProvider.generate`, running a workflow
with the **mock provider** completes all steps in seconds, while **Ollama** runs
≈60 s/step (a setting worth documenting in the user guide: use mock for live
demos).

---

## 11. Governance engine

**File:** `app/services/governance_service.py`

### Security scanner — `scan_prompt_security(text)`

Regex based, two classes:

- **Prompt injection** patterns (`INJECTION_PATTERNS`, severity HIGH):
  "ignore all previous instructions", "reveal the system prompt",
  "override safety guidelines", etc.
- **Sensitive data** patterns (`SENSITIVE_DATA_PATTERNS`, severity MEDIUM):
  email, phone, credit-card-ish digits, API keys (`sk-…`), passwords,
  account numbers.

Returns `[{category, detail, severity}]`. No LLM call; usable pre-execution.

### Policy engine

Policies are persisted as `GovernancePolicy` rows with schema:

```json
{
  "condition": {"field": "data_classification", "operator": "=", "value": "RESTRICTED"},
  "action":    {"type": "deny_external_llm", "label": "External LLM denied", "value": true}
}
```

`_matches_condition` supports operators `=`, `!=`, `in`, `contains`. Matching
rules produce **decisions** (deduped by `type`) and **violations**.

`evaluate_governance(payload, …)`:

1. **Static rules** first:
   - `RESTRICTED` → `deny_external_llm` + `require_approval`
   - `HIGH`/`CRITICAL` risk → `require_review`
   - `contains_pii` → `high_logging`
   - external sharing `ALLOWED` + CONFIDENTIAL/RESTRICTED → `DATA_EXPORT` violation
2. **Persisted policies** — any whose `condition` matches contributes its
   `action`; deny-type actions append violations.
3. `approved = no HIGH/CRITICAL severity violations`.
4. Violations are persisted as `ComplianceViolation` rows and audited as
   `GOVERNANCE_VIOLATION` (with a recorded actor when provided).

`evaluate_prompt_governance(prompt, actor)` builds the payload from a prompt's
attributes and reuses the same engine — this is what `GET /prompts/{ref}/governance`
calls.

`governance_summary()` computes the posture numbers (published, high-risk,
awaiting approval, missing owner, deprecated) plus category/risk distributions
and the 20 most recent violations, all in one pass.

---

## 12. Audit trail

**File:** `app/services/audit_service.py` (used from every mutating service)

Every mutation site calls `audit_service.record(db, event_type, actor, entity…)`
**inside the same transaction** as the change, so the event cannot be lost if the
mutation commits. Events write `AuditEvent` rows (event_type, actor,
entity_type/ref/name, details JSON, timestamp, `event_id`).

Representative event types: `PROMPT_CREATED`, `PROMPT_UPDATED`, `PROMPT_DELETED`,
`PROMPT_EXECUTED`, `PUBLISHED`, `APPROVED`, `DEPRECATED`, `RETIRED`,
`WORKFLOW_CREATED`, `WORKFLOW_EXECUTED`, `POLICY_CREATED`, `GOVERNANCE_VIOLATION`,
`USER_CREATED`.

`GET /api/v1/audit` returns `{items, total}` with `event_type` / `entity_type` /
`actor` filters and pagination; `/audit/recent` for dashboards.

---

## 13. Seeding architecture

**File:** `backend/app/seed/` (entry `seed_all()`)

`seed_all()` is **idempotent**: if a user `henry` already exists it logs and
returns, so restarts don't duplicate data. It is invoked from the FastAPI
lifespan (and the Docker command).

Order of operations:

1. `init_db()` — create tables.
2. `_seed_users` — 8 users (unique `user_id`, hashed `password`).
3. `_seed_prompts` — 68 prompts; assigns status from a **status wheel**
   (mix of PUBLISHED/APPROVED/UNDER_REVIEW/DRAFT/DEPRECATED); owner round-robin;
   computes `quality_score` with `analyse_prompt_fields`; adds inputs and
   version-1.0 snapshots; **advances the prompt counter** past 68.
4. `_seed_policies` — 5 policies (condition/action JSON).
5. `_seed_documents` — 16 M365 docs, chunked at 400 chars.
6. `_seed_knowledge_sources` — links "Executive Summary", "Project Risk
   Assessment", "Project Status", "Dataset Summary" to relevant docs.
7. `_seed_workflows` — 5 promptbooks; resolves step `prompt_name` → prompt row.
8. `_seed_analytics_rows` — synthetic execution history (capped at 40 rows per
   popular prompt) and ratings, so dashboards/analytics look alive.

Re-seeding is done by deleting the SQLite file (`prompthub.db`) and restarting —
or `uv run python -c "from app.seed import seed_all; seed_all()"`.

---

## 14. Frontend architecture

```
frontend/
  vite.config.ts        dev server, /api + /health proxy → 127.0.0.1:8000
  src/
    main.tsx            ReactDOM + QueryClientProvider + BrowserRouter
    App.tsx             route table (Layout + 10 pages)
    index.css           Tailwind base
    api/
      client.ts         fetch wrapper, JSON, error surfacing, API_BASE
      types.ts          TS mirrors of Pydantic schema
      index.ts          typed endpoint functions (grouped by domain)
    components/
      Layout.tsx        sidebar nav (badge = governance high-risk count)
      ui.tsx            Button, Card, Badge, QualityRing, StatusBadge, Spinner, ...
    lib/format.ts       time/date/markdown helpers
    pages/              Dashboard, Library, PromptDetail, Builder, Assistant,
                        Workflows, Analytics, Governance, Audit, Admin
```

### The API client

`client.ts` resolves base URL as `import.meta.env.VITE_API_URL || "/api/v1"`.
In dev the browser calls the **same origin** (`/api/v1/...`) and Vite proxies to
the backend; in Docker the built bundle embeds `VITE_API_URL` and calls the
backend directly (handled by CORS). Mutations (`POST/PUT`) send JSON bodies and
throw `Error(body)` on non-2xx so react-query surfaces them.

`index.ts` binds each endpoint to a typed function grouped by domain
(`promptsApi`, `assistantApi`, `executionApi`, `workflowsApi`,
`governanceApi`, `analyticsApi`, `auditApi`, `knowledgeApi`, `adminApi`,
`catalogApi`). Pages consume them via `useQuery`/`useMutation` with structured
query-keys so invalidation targets the right cache node.

**Notable rendering choices**

- `QualityRing` (SVG) shows `quality_score` at a glance.
- Library uses URL search params (`?q=&task=&status=&page=`) so filters survive
  refresh and are shareable.
- Workflows page renders `step_results` as a stepper with `StatusBadge`.
- Recharts renders `executions_by_day`, `top_prompts`, `execution_by_category`
  from the aggregate payload.

---

## 15. Authentication & authorization

**File:** `backend/app/security.py`, `backend/app/api/auth.py`, `backend/app/api/deps.py`

- Passwords hashed with **PBKDF2** (`hash_password` / `verify_password`).
- **API tokens** are HMAC-signed payloads (`create_token` / `decode_token`)
  containing the user id and expiry (`TOKEN_EXPIRY_MINUTES`).
- `get_current_user` dependency:
  - `ENABLE_AUTH=false` → returns the seeded demo user **henry** (ADMIN) so the
    whole app works without login;
  - `ENABLE_AUTH=true` → parses the `Authorization: Bearer <token>` header,
    decodes, loads the user, else 401.
- `require_role(*roles)` wraps `get_current_user` and enforces role membership
  (403). Currently enforced: `ADMIN` (delete prompts, admin users), and
  `GOVERNANCE`/`ADMIN` (create policies).
- `/auth/login` (`POST`) and `/auth/me` (`GET`) complete the API contract for
  future UI login.

---

## 16. Testing strategy

**Files:** `backend/tests/conftest.py`, `test_quality_engine.py`, `test_api.py`

`conftest.py`:

- Sets `DATABASE_URL` to a **temp-file SQLite** and `LLM_PROVIDER=mock`,
  `MOCK_LLM_LATENCY_MS=0` **before importing app code** (hence the `E402`
  ignore on the import).
- Runs `seed_all()` against the temp DB and exposes a FastAPI `TestClient`.

Coverage (23 tests):

| Suite | Focus |
|-------|-------|
| `test_quality_engine.py` | Rubric scores, empty → Poor, missing goal verb, rating boundaries, structured `analyse_prompt_fields` |
| `test_api.py` | Health, catalog, prompt list/filter/detail/search/versions, all four assistant modes, execution + eval metrics, workflow list + 6-step run, governance evaluate/scan/summary, analytics, audit, knowledge, policy creation |

Run:

```bash
cd backend
uv run pytest tests
uv run ruff check app tests
uv run ruff format .          # auto-format
```

Quality-engine behaviour (goal verb, degree of context, expectation markers) is
asserted with exact expected scores — the deterministic design is what makes this
possible.

---

## 17. Build, deploy & operations

### Local dev

```bash
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev        # proxy → :8000
```

### Docker compose (production-style)

- `backend/Dockerfile` — python:3.11-slim + uv sync, `CMD uvicorn`.
- `frontend/Dockerfile` — node:20-alpine, **bake** `VITE_API_URL` at build,
  serve `dist` via `vite preview`.
- `docker-compose.yml` — `postgres` (healthcheck-gated), `qdrant`, `ollama`,
  `backend` (env: postgres URL, `RAG_MODE=qdrant`, `LLM_PROVIDER=ollama`) and
  `frontend`. The backend command seeds then runs uvicorn.

### Environment-specific activation

| Desired behaviour | Configuration |
|-------------------|---------------|
| Zero-dependency demo | defaults (SQLite + `auto`→mock) |
| Fast workflow demo | `LLM_PROVIDER=mock` |
| Real local inference | Ollama running; leave `auto` or set `ollama` |
| Production storage | `DATABASE_URL=postgresql+psycopg://…` |
| Vector RAG | `RAG_MODE=qdrant` + `QDRANT_URL` |
| Real login | `ENABLE_AUTH=true` |
| Different backend port | `uvicorn --port 8005` + `VITE_PROXY_TARGET=http://127.0.0.1:8005` |

---

## 18. Data-flow walkthroughs

### Single prompt execution (request → audit)

```
Browser → POST /api/v1/executions {prompt_id, input_data, use_grounding}
  → execution_service.run_prompt
  → (RAG?) LocalRetriever.retrieve(inputs) → GroundingContext
  → LLMProvider.generate(template, system, grounding, hints)
  → evaluate_output(...) → eval_metrics
  → INSERT prompt_executions
  → INSERT audit_events (PROMPT_EXECUTED)
  → ExecutionOut JSON → React Query cache → Test execution <pre>
```

### Workflow run

```
Browser → POST /api/v1/workflows/{ref}/run {input_data}
  → workflow_service.run_workflow
  → INSERT workflow_executions (RUNNING)
  → per step: resolve input_mapping → RAG → generate → step_results
  → UPDATE workflow_executions (SUCCESS/FAILED, final_output, latency)
  → INSERT audit_events (WORKFLOW_EXECUTED)
  → WorkflowExecutionOut → Workflows page stepper
```

### Governance evaluation

```
Browser → POST /api/v1/governance/evaluate {classification, risk, flags…}
  → static rules → inserted decisions
  → loop enabled GovernancePolicies → condition match → actions/violations
  → approved = no HIGH/CRITICAL violations
  → INSERT compliance_violations (+ audit GOVERNANCE_VIOLATION)
  → GovernanceEvaluationOut → sandbox panel
```

### Prompt quality scoring

```
Builder save → POST /api/v1/prompts (PromptCreate)
  → prompt_service.create_prompt
  → analyse_prompt_fields(goal, context, source, expectations, …)
  → prompt.quality_score = score (same transaction)
  → PromptDetail (quality ring in UI)
```

---

## 19. Extending the platform

| Intent | Where to change |
|--------|-----------------|
| Add an LLM provider | New class in `app/llm/providers.py` + a branch in `factory.get_provider` |
| Add a quality rubric rule | `app/quality/engine.py` — extend markers or add component |
| Add a governed attribute | Column on `Prompt` + `GovernanceEvaluationIn` + `_matches_condition` field name + PolicyIn condition |
| Add a governance policy | `POST /api/v1/governance/policies` or seed in `governance_catalog.py` |
| Add a workflow | `POST /api/v1/workflows` or seed in `workflows_catalog.py` |
| Add a catalog prompt | Seed in `prompts_catalog.py` (template + inputs) |
| Change storage | `DATABASE_URL` only — model code is dialect-agnostic |
| Change the seed data | `app/seed/*` catalogs; delete `prompthub.db` and restart |
| Add a frontend page | New file in `src/pages/`, add a `Route` in `App.tsx`, add a nav item in `Layout.tsx` |
| Change DDL | Edit `app/models/entities.py` **and** bump/apply schema (dev: delete `.db`; prod: run a real migration) |

> **Migration note:** the current runtime uses `create_all`, which is sufficient
> for the self-hosted demo but not for evolving production schemas. For a real
> deployment, add Alembic and generate a baseline revision from `Base.metadata`
> before the first production release.
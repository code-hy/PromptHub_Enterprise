# product-spec.md — PromptHub Enterprise

## 1. Problem & Vision

Enterprise teams accumulate thousands of ad-hoc prompts across Outlook, Teams, Word, Excel and PowerPoint, with no ownership, versioning, quality bar or governance. Failed migrations, model lock-in and un-auditable AI use create operational and compliance risk.

PromptHub provides a **single, self-hosted prompt library, engineering workbench, test harness and governance control plane**. Every prompt is classified (business function, application, task, data class, risk), versioned, quality-scored, and executable via a single LLM gateway (mock / local Ollama / OpenAI-compatible) with deterministic evaluation and immutable audit.

## 2. Actors & Roles

| Actor | Role | Capabilities |
|---|---|---|
| **Author** | Creates/edits prompts | Builder, library, test execution, drafts |
| **Reviewer** | Approves quality/compliance | Governance evaluation, approve / reject / changes_requested |
| **Admin / Governance** | Operates platform | Policies, audit, user admin, analytics |
| **System** | RAG + quality engine | No LLM required for score / analysis / grounding |

Contoso demo seeds 8 users covering these roles (`backend/app/seed/users_catalog.py`); default auto-sign-in is `henry` (ADMIN) when `ENABLE_AUTH=false`.

## 3. User Stories & Acceptance Criteria

### 3.1 Library
- **As an Author** I can browse 68 seeded prompts, filter by function/task/status/risk/app, search, sort (updated/rating/executions), paginate, favourite, rate.
- *Accept:* filter counts match API `GET /api/v1/prompts`; pagination returns `total` + `items`; favourite persists per user.

### 3.2 Prompt lifecycle
- **As an Author** I draft → submit → published; reviewer can approve/reject; author can create new version.
- *Accept:* status transitions `DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED → PUBLISHED → DEPRECATED → RETIRED` (`backend/app/core/enums.py`) validated; every mutation writes `audit_events`; versions stored in `prompt_versions` with snapshot.

### 3.3 Prompt Builder & Assistant
- **As an Author** I compose goal/context/source/expectations, inputs `{{placeholders}}`, tone/format/temperature/governance flags, and get a deterministic 100-point, 9-component score with `analyse` / `improve` / `generate` / `explain`.
- *Accept:* `POST /api/v1/assistant/{analyse|improve|generate|explain}` returns `AssistantResponse` without LLM; scores stable for same input.

### 3.4 Testing (single prompt & grounded)
- **As an Author** I can Test-execute a prompt with `inputs`, choose `provider` (`auto`/`mock`/`ollama`/… ) and `model` (auto-discovers `gemma4:e2b` if present), optionally with `use_grounding` over 16 synthetic M365 docs; the panel shows `provider/model · latency · tokens` and is scrollable (`PromptDetail.tsx:328` `max-h-[55vh]`).
- *Accept:* `POST /api/v1/executions` returns `ExecutionOut` (`provider`/`model` reflect the gateway actually used); eval metrics (`instruction`, `grounding`, `overall_score`) recorded; outputs reference `sources_used` when grounded.

### 3.5 Workflows (promptbooks)
- **As an Author** I can chain prompts into a workflow (5 seeded), run it, see per-step results.
- *Accept:* `POST /api/v1/workflows/{id}/run` returns `WorkflowExecutionOut` with `step_results` + `final_output`.

### 3.6 Governance & Compliance
- **As a Governance user** I see posture (`high_risk`, `awaiting_approval`, `missing_owner`, `deprecated`), evaluate any prompt against 5 seeded policies, and view violations.
- *Accept:* `GET /api/v1/governance/summary` matches dashboard numbers; `POST /api/v1/governance/evaluate` and `/scan` produce `decisions`/`violations`; `compliance_violations` rows created on execution when `record_violations != false`.

### 3.7 Analytics & Audit
- **As an Admin** I see execution volume, success rate, ratings, time saved, daily trend, top prompts, category breakdown; every mutation is in `audit_events`.
- *Accept:* `GET /api/v1/analytics/overview` payload drives `Analytics.tsx` charts; `GET /api/v1/audit?entity_ref=PROMPT-…` powers the lifecycle flow trail.

## 4. Non-functional

- **Self-hosted, zero-deps demo:** `LLM_PROVIDER=auto` → mock fallback, `DATABASE_URL` empty → SQLite file `prompthub.db`.
- **Portable:** `docker compose up` brings `postgres` (PG), `qdrant`, `ollama`, `backend:8010`, `frontend:5173` (Vite proxies `/api` → `127.0.0.1:8010`).
- **Contract-first:** All HTTP via `openapi.yaml` generated from FastAPI (`GET /openapi.json`); frontend `frontend/src/api/*` is the typed client.
- **Observability:** `/health` (`{"status":"ok"}`), `audit_events`, `TROUBLESHOOTING.md`.

## 5. Out of scope (for this cohort)

- SSO / external IdP, RBAC beyond `USER/AUTHOR/REVIEWER/ADMIN/GOVERNANCE`.
- Multi-region / HA (single Docker Compose topology).
- Cloud deployment — see `ops/render.md` and `docs/deployment.md` for the Render blueprint; local is the default.

## 6. Acceptance environment & seed

- `SEED_DEMO_DATA=true` seeds 68 prompts, 5 workflows, 5 policies, 16 docs, 8 users on first boot; `SEED_DEMO_DATA=false` leaves an empty DB for production.
- `uuid` business IDs (`PROMPT-000001` …) guarantee stable references across environments.

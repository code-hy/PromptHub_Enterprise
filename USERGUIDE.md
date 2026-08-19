# PromptHub Enterprise — User Guide

A self-hosted enterprise **AI prompt library, engineering, testing and governance
platform**. This guide walks through installation, configuration, every screen in
the app, and the common day-to-day tasks.

> **Not sure where to start?** Follow [Quick start](#quick-start), then the
> [Guided scenarios](#guided-scenarios).

---

## Table of contents

- [1. Overview](#1-overview)
- [2. What's included](#2-whats-included)
- [3. Architecture](#3-architecture)
- [4. Quick start](#4-quick-start)
- [5. Configuration](#5-configuration)
- [6. LLM providers](#6-llm-providers)
- [7. The demo dataset](#7-the-demo-dataset)
- [8. The user interface](#8-the-user-interface)
- [9. Guided scenarios](#9-guided-scenarios)
- [10. Prompt lifecycle](#10-prompt-lifecycle)
- [11. Governance model](#11-governance-model)
- [12. API reference](#12-api-reference)
- [13. Common tasks](#13-common-tasks)
- [14. Troubleshooting](#14-troubleshooting)
- [15. Security notes](#15-security-notes)

---

## 1. Overview

PromptHub Enterprise gives a single-window platform for:

1. **Curating a prompt library** — centrally managed, versioned, classified and
   rated prompts across business functions, tasks and M365 applications.
2. **Engineering better prompts** — a deterministic quality rubric scores any
   prompt out of 100 against nine components and gives concrete fixes.
3. **Testing prompts** — run any prompt against a mock LLM or a real model, with
   optional grounding on a company knowledge corpus.
4. **Automating prompt chains** — workflows ("promptbooks") that sequence prompts
   and pipe outputs between steps.
5. **Governance & audit** — policy enforcement, classification/risk posture,
   an evaluation sandbox, security scanning and an immutable audit log.

Everything runs **offline and self-contained** by default (SQLite + mock LLM), so
the demo works with zero cloud dependencies. You can flip to PostgreSQL, Qdrant
and Ollama/OpenAI for a production-style deployment.

---

## 2. What's included

| Area | Capabilities |
|------|--------------|
| **Library** | 68 seeded prompts; filter by function/task/application/status/risk; search; sort (updated, rating, executions, name); pagination; favourites; star ratings |
| **Builder** | Structured authoring — goal, context, source, expectations, system instruction, inputs (`{placeholders}`), tone, output format, temperature, tags, governance attributes; edit existing prompts; track every change |
| **Assistant** | 4 modes — `analyse`, `improve`, `generate`, `explain` — powered by a 100-point, 9-component deterministic quality engine (no LLM required) |
| **Testing** | Run prompts with mock or real LLMs, with/without RAG grounding; per-run eval metrics and sources recorded |
| **Workflows** | 5 seeded promptbooks; run them step-by-step with output chaining and elapsed-time cost accounting |
| **Governance** | 5 seeded policies; evaluation sandbox; risk distribution; compliance violations; security scan (prompt injection / sensitive content) |
| **Analytics** | Execution volume, success rate, average rating, minutes saved, daily trend, top prompts, category + model usage |
| **Audit** | Immutable `audit_events` log — every mutation is recorded with actor, entity and detail |
| **Admin** | User directory with roles and permissions |
| **API** | Full REST API under `/api/v1`, OpenAPI docs at `/docs` |

---

## 3. Architecture

```
┌──────────────────────────────────────────────┐
│  Frontend  React + TypeScript (Vite, 5173)  │
│  Tailwind · react-query · recharts          │
└─────────────────────┬────────────────────────┘
                      │  /api  (dev proxy → backend)
┌─────────────────────▼────────────────────────┐
│  Backend   FastAPI + SQLAlchemy 2.0  (:8000) │
│                                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ │
│  │ quality │ │  rag    │ │  llm    │ │seed   │ │
│  │ engine  │ │retriever│ │ factory │ │dataset│ │
│  └─────────┘ └─────────┘ └─────────┘ └───────┘ │
│  · services (prompts, workflows, governance…)  │
│  · models / schemas (PostgreSQL or SQLite)     │
└────────────────────────────────────────────────┘

External (optional): PostgreSQL · Qdrant · Ollama · OpenAI-compatible gateways
```

Routing:

- `/api/v1` — REST API (catalog, prompts, assistant, executions, workflows,
  governance, analytics, audit, admin, knowledge, auth)
- `/docs` — interactive OpenAPI documentation
- `/health` — liveness check (reports the active LLM provider)

---

## 4. Quick start

### Prerequisites

| Tool | Purpose | Notes |
|------|---------|-------|
| Python 3.11+ | Backend runtime | any 3.11/3.12 works |
| **uv** | Python package manager | `pip install uv` or via installer |
| Node.js 18+ | Frontend build | includes `npm` |
| Docker (optional) | Full compose stack | only needed for `docker compose` |

> Local dev uses **SQLite** and a **mock LLM** — nothing else to install.

### Option A — backend only

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>
- First boot auto-creates `../prompthub.db` and seeds the demo dataset.

### Option B — full stack (backend + frontend)

Terminal 1 — backend:

```powershell
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

Terminal 2 — frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open **<http://localhost:5173>**. The Vite dev server proxies `/api` to the
backend on `:8000`, so there's no CORS configuration to mess with.

### Option C — Docker compose (production-style)

```powershell
docker compose up --build
```

Starts `postgres` (16), `qdrant`, `ollama`, the backend and the frontend. The
backend container runs the seed automatically on start. The frontend is served
at <http://localhost:5173> and talks to the API at <http://localhost:8000/api/v1>.

> **Port in use?** See [Troubleshooting → Port conflicts](#port-conflicts).

---

## 5. Configuration

Copy `.env.example` to `.env` at the **repository root** and adjust:

```powershell
Copy-Item .env.example .env
```

Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *(empty — SQLite)* | `postgresql+psycopg://user:pass@host:5432/db` switches to PostgreSQL |
| `LLM_PROVIDER` | `auto` | `auto` \| `mock` \| `ollama` \| `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama endpoint |
| `OLLAMA_MODEL` | `qwen3:1.7b` | Default Ollama model |
| `OPENAI_API_KEY` | *(empty)* | Enables the OpenAI-compatible provider |
| `OPENAI_MODEL` | `gpt-4o-mini` | Default OpenAI model |
| `RAG_MODE` | `local` | `local` (keyword, zero deps) \| `qdrant` (vector) |
| `QDRANT_URL` | `http://localhost:6333` | Vector store endpoint |
| `ENABLE_AUTH` | `false` | `false` = auto sign-in as demo user; `true` = password login |
| `SECRET_KEY` | dev default | **Change in production** (HMAC token signing) |
| `TOKEN_EXPIRY_MINUTES` | `720` | Bearer token lifetime |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:4173` (+127.0.0.1 forms) | Allowed frontend origins |

Environment variables always override the `.env` file. In the Docker stack the
env is supplied by `docker-compose.yml`.

---

## 6. LLM providers

The LLM layer (`backend/app/llm/`) is selected at startup by `LLM_PROVIDER`:

| Provider | Behaviour | When to use |
|----------|-----------|-------------|
| `auto` | Uses Ollama if reachable on `OLLAMA_BASE_URL`, otherwise falls back to the mock provider | **Default** — best of both worlds |
| `mock` | Deterministic template-based responses. Instant, no network, no cost. Every execution returns consistent output so tests and workflow demos finish in seconds | CI, demos, offline dev |
| `ollama` | Local inference via Ollama (e.g. `qwen3:1.7b`). Real output, ~seconds per call | Realistic local evaluation |
| `openai` | Any OpenAI-compatible API (native or `AZURE_OPENAI` gateways) | Production usage |

Notes:

- **Mock latency** is controlled by `MOCK_LLM_LATENCY_MS` (tests set `0`).
- **Workflow runs are synchronous.** With Ollama each step takes ~60 s, so a
  6-step workflow is ~6 minutes. Set `LLM_PROVIDER=mock` for a fast demo.
- The mock provider is deterministic given the same input, which keeps the
  quality/analytics demo stable across reboots.

---

## 7. The demo dataset

On first boot the backend seeds a deterministic enterprise dataset:

**Users (8)** — all share password `password` (only relevant with `ENABLE_AUTH=true`):

| Username | Name | Role | Department |
|----------|------|------|------------|
| `henry` | Henry | **ADMIN** | DATA_ANALYTICS |
| `david.okafor` | David Okafor | **ADMIN** | IT |
| `olivia.brown` | Olivia Brown | **GOVERNANCE** | LEGAL |
| `sarah.chen` | Sarah Chen | **REVIEWER** | PROJECT_MANAGEMENT |
| `priya.sharma` | Priya Sharma | **REVIEWER** | RISK |
| `emily.wilson` | Emily Wilson | **AUTHOR** | FINANCE |
| `marco.rossi` | Marco Rossi | **AUTHOR** | HR |
| `james.taylor` | James Taylor | **USER** | SALES |

Roles control what an account may do:

| Role | Capabilities |
|------|--------------|
| `USER` | Browse, search, favourite, execute prompts |
| `AUTHOR` | + create/edit prompts, propose changes |
| `REVIEWER` | + approve/reject lifecycle transitions |
| `GOVERNANCE` | + create/manage policies, governance checks |
| `ADMIN` | + delete prompts, manage users, everything above |

> With `ENABLE_AUTH=false` (default) the demo signs in automatically as **henry**
> (`ADMIN`), so every feature is visible out of the box.

**Prompts (68)** across 13 business functions (FINANCE, HR, SALES, LEGAL,
DATA_ANALYTICS, PROJECT_MANAGEMENT, OPERATIONS, EXECUTIVE, MARKETING, IT, RISK,
PROCUREMENT, CUSTOMER_SERVICE), 12 tasks (CREATE, ANALYSE, SUMMARISE, EXTRACT,
CLASSIFY, RECOMMEND, EXPLAIN, COMPARE, REWRITE, TRANSLATE, TRANSFORM, ...) and 6
M365 applications (WORD, EXCEL, OUTLOOK, POWERPOINT, TEAMS, GENERIC_AI). Each
has a deterministic quality score, structured attributes, inputs and version 1.0.

**Workflows (5)**:

| Workflow | Steps | Story |
|----------|-------|-------|
| Executive Project Review | 6 | emails → risks → issues → impact → summary → actions (the "45 minutes to 5 minutes" flagship) |
| Weekly Meeting Triage | 5 | transcript → decisions → actions → risks → follow-up email |
| Inbox Zero | 4 | priorities → thread summary → actions → follow-ups |
| Data Quality Review | 4 | assessment → summary → outliers → data dictionary |
| Executive Deck Builder | 3 | report → deck outline → speaker notes |

**Governance policies (5)**:

| Policy | Rule → action | Severity |
|--------|---------------|----------|
| Restricted data must stay local | classification `RESTRICTED` → deny external LLM | HIGH |
| High risk prompts require review | risk `HIGH`/`CRITICAL` → human review | MEDIUM |
| PII triggers enhanced logging | `contains_pii` → high logging | LOW |
| Confidential data cannot be shared externally | `CONFIDENTIAL`/`RESTRICTED` → prohibit share | MEDIUM |
| Customer data requires evidence | `contains_customer_data` → require evidence | MEDIUM |

**Company knowledge (16 documents)** — synthetic Contoso M365 corpus
(Outlook/Teams/Word/Excel/PowerPoint) used for RAG grounding. Retrievable under
analytics, and referenceable as sources during execution.

---

## 8. The user interface

The app has a left-hand navigation rail. Below is each screen and what you can do there.

### Dashboard (`/`)

- **Stat cards** — prompts, executions, success rate, minutes saved, average
  rating.
- **Top prompts by execution** — jump to the most-used prompts.
- **Governance posture** — high-risk, awaiting approval, missing owner,
  deprecated counts.
- **Recently executed** — live look at execution history.
- **Highest quality prompts** — quick links into the library.

### Library (`/library`)

The searchable, filterable catalogue. In one page you can:

1. **Search** by free text (filter as you type, Enter to apply).
2. **Filter** by business function, task, status and risk level.
3. **Sort** by recently updated, top rated, most used, or name A–Z.
4. **Paginate** through results (12 per page).
5. Click a card to open the full **Prompt detail** page.

### Prompt detail (`/prompts/:id`)

Click any prompt card to land here:

- **Header** — name, status, version, description, category chips and the
  **quality ring** (out of 100).
- **Prompt template** — the rendered template plus system instruction.
- **Structured attributes** — goal, context, source, expectations, audience,
  tone, output format, temperature, plus governance flags.
- **Versions** — every version with approval status and change note.
- **Test execution** — fill the declared inputs, then:
  - **Run (mock)** — instant deterministic output.
  - **Run with grounding** — adds RAG retrieval over the Contoso corpus and
    reports which document sources were used.
- **Lifecycle** — drive the state machine: submit for review, approve, reject,
  publish, deprecate, retire.
- **Governance** — run a live policy check against this prompt.

### Prompt Builder (`/builder`, `/builder/:id`)

Create or edit a prompt:

- **Basics** — name, description, business function, application, task, tags.
- **Prompt structure** — goal, context, source, expectations, system
  instruction, and the template with `{placeholder}` inputs.
- **Inputs** — add typed inputs (TEXT / NUMBER / SELECT / MULTILINE), mark
  required, give descriptions and samples.
- **Output & tone** — audience, tone, output format, max length, temperature,
  manual-time-saved estimate.
- **Governance** — classification, risk level, external-sharing policy, and
  flags (PII, financial data, customer data, requires approval, requires
  evidence, no unsupported claims, ask clarification).
- **Assistant panel** — with the template filled, run `analyse` / `improve` /
  `generate` / `explain`, then click **Apply improved template** to pull the
  assistant's improved version straight into the textarea.

### Assistant (`/assistant`)

A scratchpad for evaluating any prompt text (no need to save it first):

- Select a mode: **Analyse** (score + rubric), **Improve** (returns a stronger
  prompt), **Generate** (draft from intent + function/task), **Explain**.
- The result shows: score badge, per-component rubric breakdown, missing/present
  components, recommendations, and the improved/generated/explained text.
- **Security scan** — checks the text for prompt-injection and sensitive-content
  indicators without calling the LLM.

### Workflows (`/workflows`)

List of the 5 seeded promptbooks. Each card shows the step chain with sequence
numbers and the per-step prompt. Click **Run workflow** to execute the chain:

- Inputs can be mapped; the run shows each step with its status and output.
- A **final output** section collates the last step's result.
- Elapsed time is reported; the "minutes saved" value comes from the manual vs
  AI time estimates on the workflows and prompts.

> With `LLM_PROVIDER=ollama` a run takes roughly 60 s per step. Use the mock
> provider for an instant demo.

### Analytics (`/analytics`)

- Stat strip — executions, minutes saved, average latency/tokens, average rating.
- **Executions per day** line chart.
- **Top prompts by executions** horizontal bar chart.
- **Executions by category** pie chart.
- (Productivity detail also available via `/api/v1/analytics/productivity`.)

### Governance (`/governance`)

- Stat strip — total/published prompts, high-risk, awaiting approval, deprecated.
- **Risk distribution** — proportional bars for LOW / MEDIUM / HIGH.
- **Violations** — compliance violations raised by policy evaluation.
- **Evaluation sandbox** — pick classification, risk, external-sharing, provider
  and data flags, hit **Evaluate**, and see the policy decisions recorded for
  that combination.
- **Active policies** — the 5 seeded rules with their conditions and actions
  rendered as JSON.

### Audit Log (`/audit`)

Every mutation in one place: event type (e.g. `PROMPT_CREATED`, `PROMPT_UPDATE_D`,
`PUBLISHED`, `POLICY_CREATED`, `EXECUTION_RUN`), actor, entity, and a JSON detail.
Filter by event type, search by actor, and page through the history.

### Admin (`/admin`)

The seeded user directory with roles, departments and titles — the same data the
`/api/v1/admin/users` endpoint serves.

---

## 9. Guided scenarios

### Scenario 1 — Find and run a prompt

1. Open **Library** → type `meeting` in Search → filter **Task = SUMMARISE**.
2. Click **Meeting Summary**.
3. In **Test execution**, enter a sample meeting transcript or leave the provided
   sample.
4. Click **Run (mock)** — instant answer. Then **Run with grounding** and note
   the "Sources:" line listing Contoso documents used.
5. Back in the header, note the **quality ring** and check **Governance** →
   **Check against policies**.

### Scenario 2 — Build a prompt with the Assistant

1. Go to **Builder** → **+ Add input**, create a `topic` input, and write a
   rough template: `Summarise the key points about {topic} for our exec board.`
2. Click **analyse** in the Assistant panel — the rubric should flag missing
   *expectations*, *source*, *output format*, etc.
3. Click **improve**, then **Apply improved template**.
4. Fill in Basics/Governance, then **Create prompt**. It appears in the Library
   as `DRAFT`.
5. From the detail page, **Submit for review** → (as a reviewer) **Approve** →
   **Publish**.

### Scenario 3 — Run an automated workflow

1. Open **Workflows** → **Inbox Zero**.
2. Click **Run workflow**. Newly-created executions may need inputs; the flagship
   **Executive Project Review** accepts a raw project brief.
3. Watch each step execute in order — this is the "45 minutes to 5 minutes"
   claim in action. The **final output** lands at the bottom.

### Scenario 4 — Test governance decisions

1. Open **Governance** → **Evaluation sandbox**.
2. Set **Classification = RESTRICTED**, **Provider = openai**, keep external
   sharing **PROHIBITED** → **Evaluate**.
3. Expect a **deny**-style decision (RESTRICTED data must stay local) with the
   matching violation shown.
4. Now try **Risk = HIGH** and **External sharing = ALLOWED** — the high-risk
   review policy should trigger.

---

## 10. Prompt lifecycle

Prompt status is an explicit state machine. Transitions are triggered from the
detail page's **Lifecycle** panel (or the API):

```
DRAFT ── submit_for_review ──► UNDER_REVIEW ── approve ──► APPROVED ── publish ──► PUBLISHED
  ▲                           │
  └────────── reject ◄────────┘
PUBLISHED ── deprecate ──► DEPRECATED ── retire ──► RETIRED
```

| Action | From | To | Notes |
|--------|------|----|-------|
| `submit_for_review` | DRAFT | UNDER_REVIEW | Author proposes the prompt |
| `approve` | UNDER_REVIEW | APPROVED | Reviewer sign-off |
| `reject` | UNDER_REVIEW | DRAFT | Sentinel back to author with a note |
| `publish` | APPROVED | PUBLISHED | Visible in the library for everyone |
| `deprecate` | PUBLISHED | DEPRECATED | Still browseable, but withdrawn |
| `retire` | DEPRECATED | RETIRED | Removed from active use |

Editing an already-published prompt auto-creates a new **version** snapshot so
history is preserved.

---

## 11. Governance model

- Every prompt carries **classification** (PUBLIC, INTERNAL, CONFIDENTIAL,
  RESTRICTED), a **risk level** (LOW/MEDIUM/HIGH/CRITICAL), an **external-sharing**
  policy, and data-content flags.
- The **policy engine** matches those attributes against enabled policies
  (conditions → actions) and returns a decision per policy plus an overall
  `approved` boolean.
- Governance decisions are surfaced three ways:
  1. **per prompt** — the Governance panel on the detail page;
  2. **ad-hoc** — the Evaluation sandbox with arbitrary attributes;
  3. **in bulk** — the summary/violations screens.
- The **security scanner** inspects text for prompt-injection patterns and
  sensitive-data triggers without an LLM call.

---

## 12. API reference

All endpoints are prefixed `/api/v1`. Interactive docs: <http://localhost:8000/docs>.

**System**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness + active LLM provider |

**Catalog & library**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/catalog` | All filter dropdown values + models/providers |
| GET | `/prompts` | List/search/filter/sort/paginate |
| POST | `/prompts` | Create a prompt |
| GET | `/prompts/{ref}` | Prompt detail + inputs + quality |
| PUT | `/prompts/{ref}` | Update (auto-versions if published) |
| DELETE | `/prompts/{ref}` | Delete (ADMIN) |
| POST | `/prompts/{ref}/clone` | Duplicate a prompt |
| POST | `/prompts/{ref}/flow` | Lifecycle: publish/deprecate/retire/submit/approve/reject |
| POST | `/prompts/{ref}/rate` | Give a star rating + feedback |
| POST | `/prompts/{ref}/favourite` | Toggle favourite |
| GET | `/prompts/{ref}/governance` | Policy evaluation for this prompt |
| GET | `/prompts/{ref}/versions` | Version history |
| GET | `/prompts/{ref}/versions/{version}` | Version snapshot |
| GET | `/prompts/{ref}/compare` | Diff two versions |

**Assistant & LLM**

| Method | Path | Description |
|--------|------|-------------|
| POST | `/assistant/analyse` | Score + rubric breakdown |
| POST | `/assistant/improve` | Return an improved prompt |
| POST | `/assistant/generate` | Generate a prompt from intent |
| POST | `/assistant/explain` | Explain what the prompt asks |
| POST | `/executions` | Run a prompt (mock/LLM, optional grounding) |
| GET | `/executions`, `GET /executions/{id}` | Execution history / detail with eval metrics |

**Workflows**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/workflows`, `GET /workflows/{ref}` | List / detail |
| POST | `/workflows` | Create a workflow |
| POST | `/workflows/{ref}/run` | Execute a workflow with inputs |
| GET | `/workflows/{ref}/executions` | Recent runs for a workflow |

**Governance & analytics & audit**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/governance/policies` | List policies |
| POST | `/governance/policies` | Create a policy (GOVERNANCE/ADMIN) |
| POST | `/governance/evaluate` | Sandbox evaluation |
| GET | `/governance/summary` | Posture summary + distributions |
| GET | `/governance/violations` | Compliance violations |
| GET | `/analytics/overview` | KPI overview + charts data |
| GET | `/analytics/productivity` | Time-saved per prompt detail |
| GET | `/audit` | Audit log (filter + paginate) |
| GET | `/knowledge/documents` | Browse the Contoso corpus |
| GET | `/admin/users` | User directory (ADMIN) |

Example — run a prompt:

```bash
curl -X POST http://localhost:8000/api/v1/executions \
  -H "Content-Type: application/json" \
  -d '{"prompt_id": 1, "input_data": {"documents": "Q3 board pack"}, "use_grounding": true}'
```

---

## 13. Common tasks

| Task | How |
|------|-----|
| Re-run tests | `cd backend; uv run pytest tests` |
| Lint/format | `cd backend; uv run ruff check app tests; uv run ruff format` |
| Re-seed the demo | Delete `prompthub.db`, restart the backend (seed runs on boot) |
| Use PostgreSQL | Set `DATABASE_URL` in `.env`; restart backend |
| Use Ollama | Start Ollama, set `OLLAMA_MODEL`; or just leave `auto` |
| Use a different port | Pass `--port 8005` to uvicorn; set `VITE_PROXY_TARGET=http://127.0.0.1:8005` before `npm run dev` |
| Enable real login | Set `ENABLE_AUTH=true`; login with any seeded user (password `password`) |
| Extract API base URL | `VITE_API_URL` in the frontend build (default `/api/v1`) |

---

## 14. Troubleshooting

### Port conflicts

> `[Errno 10048] ... only one usage of each socket address ...`

Something already holds the port (often a previous server, or a background
process from an IDE/agent). Three fixes:

1. **Use a different port**:

   ```powershell
   uv run uvicorn app.main:app --port 8005
   # frontend: $env:VITE_PROXY_TARGET="http://127.0.0.1:8005"; npm run dev
   ```

2. **Free the port** (Windows):

   ```powershell
   $c = Get-NetTCPConnection -LocalPort 8000 -State Listen
   Stop-Process -Id $c.OwningProcess -Force
   ```

3. **`make run-stack` ports** — if Docker ports (5432, 6333, 11434) collide,
   change the mapping in `docker-compose.yml`.

### Stale/odd data after a restart

The seed only runs when the DB is empty. To rebuild the demo dataset cleanly:

```powershell
# stop the backend first
Remove-Item ..\prompthub.db   # from backend/, or delete prompthub.db from repo root
uv run uvicorn app.main:app --port 8000
```

> On Windows, kill any running `uvicorn` first — the SQLite file is locked while
> a server holds it.

### Workflow runs are slow

This is expected with Ollama (~60 s/step). For fast demos:

```powershell
$env:LLM_PROVIDER="mock"; uv run uvicorn app.main:app --port 8000
```

### Frontend loads but API calls fail

- Confirm the backend prints the expected startup and that `http://localhost:8000/health` returns `{"status":"ok",...}`.
- If you changed the backend port, restart `npm run dev` with
  `VITE_PROXY_TARGET` pointing at the new port.
- The app auto-signs in as `henry` (ADMIN) — if you enabled `ENABLE_AUTH=true`,
  you must log in first; otherwise you'll see 401s.

### "Prompt not found" / missing data

The seed was skipped because the DB already existed. Delete `prompthub.db` and
restart, or run `cd backend; uv run python -c "from app.seed import seed_all; seed_all()"`.

---

## 15. Security notes

- The **default demo setup is single-user and not hardened** — do not expose it
  on the public internet as-is.
- Before a production deployment:
  - set a strong `SECRET_KEY`;
  - set `ENABLE_AUTH=true` and manage user passwords;
  - use PostgreSQL and Qdrant instead of local SQLite;
  - restrict `CORS_ORIGINS` to your real frontend origin;
  - put HTTPS in front (App Gateway / ingress).
- The audit log is append-only by convention — keep it in a durable database in
  production.
- Never commit `.env` (it is gitignored). `.env.example` contains only
  placeholders.
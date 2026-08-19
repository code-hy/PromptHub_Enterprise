# PromptHub Enterprise — Implementation Guide

A practical, hands-on companion to TECHNICAL_GUIDE.md. This document focuses on
**how the codebase is organized, how to build and run it step by step, how to
extend it, and how to take it to production**. Follow it in order if you are
picking up the repository fresh.

---

## Table of contents

- [1. Repository layout](#1-repository-layout)
- [2. Setup checklist](#2-setup-checklist)
- [3. Running the platform](#3-running-the-platform)
- [4. Working through the code](#4-working-through-the-code)
- [5. Implementation walkthroughs](#5-implementation-walkthroughs)
- [6. Extending the platform](#6-extending-the-platform)
- [7. Testing](#7-testing)
- [8. Production hardening](#8-production-hardening)
- [9. CI/CD suggestions](#9-cicd-suggestions)
- [10. Common implementation gotchas](#10-common-implementation-gotchas)

---

## 1. Repository layout

```
Enterprise_Prompts/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers (1 per domain) — never logic here
│   │   ├── core/enums.py   # shared enumerations
│   │   ├── llm/            # LLMProvider abstraction + factory
│   │   │   ├── base.py     # ABC, GenerationResult, GroundingContext
│   │   │   ├── mock.py     # deterministic mock provider
│   │   │   ├── providers.py# ollama / openai / litellm
│   │   │   └── factory.py  # get_provider("auto"|…) + model discovery
│   │   ├── models/entities.py   # SQLAlchemy models = the DDL contract
│   │   ├── quality/        # deterministic quality rubric + assistant helpers
│   │   ├── rag/            # LocalRetriever (TF keyword) + factory
│   │   ├── schemas/api.py  # Pydantic request/response models
│   │   ├── seed/           # demo dataset (users, prompts, workflows, docs)
│   │   ├── services/       # business logic per domain
│   │   ├── config.py       # pydantic-settings: .env + env vars
│   │   ├── database.py     # engine, SessionLocal, get_db, init/reset
│   │   ├── ids.py          # sequence-backed business-formatted IDs
│   │   ├── security.py     # PBKDF2, HMAC tokens, roles, demo user
│   │   └── main.py         # app factory, lifespan (init db + seed)
│   ├── tests/
│   │   ├── conftest.py     # temp SQLite + mock provider + seeded client
│   │   ├── test_api.py
│   │   └── test_quality_engine.py
│   ├── pyproject.toml      # deps, ruff config, pytest config
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── main.tsx / App.tsx / index.css
│   │   ├── api/            # client, typed endpoints, schema mirrors
│   │   ├── components/     # Layout + shared UI primitives
│   │   ├── pages/          # 10 feature pages
│   │   └── lib/format.ts
│   ├── vite.config.ts      # dev proxy → 127.0.0.1:8000
│   ├── tailwind.config.js / postcss.config.cjs
│   └── Dockerfile
├── docker-compose.yml      # postgres + qdrant + ollama + backend + frontend
├── Makefile                # install / seed / backend / frontend / test / lint
├── .env.example
├── .gitignore
└── README.md · USERGUIDE.md · TECHNICAL_GUIDE.md · IMPLEMENTATION_GUIDE.md
```

**Golden rules of this codebase:**

1. Routers only parse/validate + call a service. Keep routes thin.
2. Services own transactions and audit calls. A mutation that doesn't write an
   `audit_events` row is probably incomplete.
3. `app/models/entities.py` is the source of truth for schema. SQLite is the
   dev dialect, PostgreSQL is production — write portable SQLAlchemy.
4. ID generation always goes through `app/ids.py` (predictable, human-readable,
   DB-independent).
5. Never hardcode a model call — go through `llm/factory.get_provider`.

---

## 2. Setup checklist

| Requirement | Verify |
|-------------|--------|
| Python | `python --version` → 3.11+ |
| uv | `uv --version` |
| Node.js | `node --version` → 18+ |
| Git | `git --version` |

```powershell
git clone https://github.com/code-hy/PromptHub_Enterprise.git
cd PromptHub_Enterprise
uv sync --active --directory backend   # or: cd backend; uv sync
cd frontend && npm install && cd ..
```

Optionally seed a root `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

The demo runs with zero external services, so you can skip `.env` entirely.

---

## 3. Running the platform

### Backend

```powershell
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

What happens on boot (`main.py` lifespan):

```
init_db()            → create_all()
seed_all()           → shows "Seed already present, skipping" if DB exists
```

Sanity: <http://localhost:8000/docs> (OpenAPI), <http://localhost:8000/health>.

### Frontend

```powershell
cd frontend
npm run dev
# → http://localhost:5173, proxies /api + /health to 127.0.0.1:8000
```

### Everything via Docker

```powershell
docker compose up --build
```

Use the app at <http://localhost:5173>; API at <http://localhost:8000/api/v1>.

---

## 4. Working through the code

Start reading in this order — each layer builds on the previous:

1. **`backend/app/config.py`** — every knob lives here (`Settings`).
2. **`backend/app/database.py`** — how sessions are made and handed to routes.
3. **`backend/app/models/entities.py`** — the data model (grep `__tablename__`).
4. **`backend/app/schemas/api.py`** — the API surface (what the frontend sees).
5. **`backend/app/api/*.py`** — routes; follow one, e.g. `executions.py`.
6. **`backend/app/services/*.py`** — the orchestration logic.
7. **`backend/app/llm/factory.py` + `llm/base.py`** — how models are invoked.
8. **`backend/app/rag/retriever.py`** — grounding.
9. **`backend/app/quality/engine.py`** — the scoring core.
10. **`frontend/src/api/index.ts`** — how the frontend calls everything.
11. **`frontend/src/pages/*.tsx`** — how the UI consumes it.

**Tracing one feature end-to-end: "Run a prompt"**

| Layer | File | What happens |
|-------|------|--------------|
| UI | `src/pages/PromptDetail.tsx` | `executionApi.run(...)` → `runExecution(useGrounding)` |
| API client | `src/api/index.ts` → `client.ts` | `POST /api/v1/executions` JSON |
| Route | `app/api/executions.py` | validate `ExecutionRequest`, load prompt |
| Service | `app/services/execution_service.py` | template → RAG → LLM → eval → persist |
| LLM | `app/llm/factory.py` | provider chosen from config |
| Audit | `app/services/audit_service.py` | `PROMPT_EXECUTED` event |

---

## 5. Implementation walkthroughs

### 5.1 Add a new LLM provider (e.g. the "Acme" HTTP gateway)

1. `backend/app/llm/providers.py` — subclass `LLMProvider`, implement
   `generate(...)`, set `name`, `model_name`; implement `list_models()` if the
   gateway exposes a model list. Use `self._measure(fn)` to time calls and fill
   `latency_ms`/`tokens` on the returned `GenerationResult`.
2. `backend/app/llm/factory.py` — add a `selected == "acme"` branch returning
   `AcmeProvider(settings.acme_base_url, settings.acme_model, settings.acme_key)`;
   register a label in `provider_options()`.
3. `backend/app/config.py` — add `acme_base_url: str = "…"`, `acme_model`,
   `acme_api_key` fields so they flow from `.env`.
4. `frontend/Dockerfile`/`.env.example` — document the new variables.
5. Test — add a unit test that `get_provider("acme")` returns the right class.

No other code needs to change: `execution_service` and `workflow_service` already
go through `get_provider()`.

### 5.2 Add a governance policy at runtime vs seed

Runtime (API — GOVERNANCE/ADMIN role):

```bash
curl -X POST http://localhost:8000/api/v1/governance/policies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Financial data must be reviewed",
    "description": "Prompts touching financial data require human review.",
    "condition": {"field": "contains_financial_data", "operator": "=", "value": true},
    "action": {"type": "require_review", "label": "Human review required", "value": true},
    "severity": "MEDIUM"
  }'
```

Seed (part of the demo dataset): append the dict to
`backend/app/seed/governance_catalog.py`; `seed_all()` picks it up on a fresh DB
(skip logic: existing `henry` user). To force a rebuild: delete `prompthub.db`
and restart.

The generic engine (`_matches_condition` with `=`, `!=`, `in`, `contains`) means
new policies rarely require code changes.

### 5.3 Add a prompt to the catalog

Append a dict to `backend/app/seed/prompts_catalog.py`:

```python
{
    "name": "Vendor Contract Risk",
    "description": "Summarise contractual risk from a procurement contract.",
    "business_function": "PROCUREMENT",
    "application": "WORD",
    "task": "ANALYSE",
    "goal": "Identify high-risk clauses in the contract.",
    "context": "We are onboarding a new software vendor.",
    "source": "Use only the supplied contract text.",
    "expectations": "Return a markdown table of risks with severity and mitigation.",
    "template": "Analyse the following contract: {{contract}}. List risks...",
    "risk_level": "MEDIUM",
    "inputs": [{"name": "contract", "type": "TEXT", "required": True}],
}
```

`?` Re-seed as above; the prompt gets an ID, a deterministic quality score and a
v1.0 version automatically.

### 5.4 Add a workflow

Either via `POST /api/v1/workflows` (payload `WorkflowCreate` with steps of
`{sequence, name, prompt_id, input_mapping, continue_on_failure}`) or by appending
to `backend/app/seed/workflows_catalog.py` (steps reference prompts by **name**,
resolved to rows during seed).

`input_mapping` grammar supported by `_resolve_input`:

| Source value | Resolves to |
|--------------|-------------|
| `input.some_field` | `input_data["some_field"]` from the run payload |
| `Step_2.output` (regex `step_(\d+)\.output`, case either) | output of the 2nd completed step |
| any other key | the run payload key itself (fallback) |

### 5.5 Wire a new frontend page

1. Create `frontend/src/pages/MyPage.tsx` (export a default component).
2. Add an icon + route entry in `src/components/Layout.tsx` (`NAV` array).
3. Register the route in `src/App.tsx`.
4. Add typed API functions in `src/api/index.ts` + types in `types.ts`.
5. Use `useQuery`/`useMutation` with stable query keys so invalidation works.

---

## 6. Extending the platform

| Change you want | Files touched | Guidance |
|-----------------|---------------|----------|
| New LLM provider | `llm/providers.py`, `llm/factory.py`, `config.py` | Implement `generate`; reuse `_measure` |
| New quality signal | `quality/engine.py` | Add markers / component + weight; update `_MAXX` and docs |
| New prompt attribute | `models/entities.py`, `schemas/api.py`, `seed`, Builder form | Keep Pydantic + ORM in sync |
| New policy on data attribute | `GovernanceEvaluationIn` + policy seed | Engine is generic |
| New audit consumer | `audit_service.record(...)` at mutation site | Always in-transaction |
| New report chart | `analytics_service` + `Analytics.tsx` (recharts) | Return aggregates, render client-side |
| Change DB dialect | `config.py` (`DATABASE_URL`) | Code is portable; verify dialect-specific queries (e.g. JSON columns) separately |
| Real migrations | Add Alembic, baseline from metadata | See §8 |

**Naming conventions:** routers are thin (verb: `list_*`, `get_*`, `create_*`),
services own verbs, IDs are `next_*_id(db)`, schemas mirror entity field names.

---

## 7. Testing

```powershell
cd backend
uv run pytest -q            # 23 tests
uv run ruff check app tests
uv run ruff format --check .
```

`conftest.py` notes:

- Drops the temp DB, sets mock LLM (`MOCK_LLM_LATENCY_MS=0`) **before** importing
  app code.
- `TestClient(app)` triggers the lifespan, so the seed runs against the temp DB.
- `E402` is ignored for `conftest.py` because env vars must be set before imports.

To add a test: mirror an existing one in `test_api.py` (route → service) or the
deterministic assertions in `test_quality_engine.py` (e.g. exact expected score
for a known prompt).

---

## 8. Production hardening

Do these before exposing anything to real users:

1. **Secrets** — set a strong `SECRET_KEY`, rotate demo password hashes, remove
   the `password` default.
2. **Auth** — `ENABLE_AUTH=true`, register real users, decide token lifetime.
3. **Storage** — `DATABASE_URL=postgresql+psycopg://…` (managed PG: backups,
   monitoring). Enable `pool_pre_ping` (already default for PG).
4. **Migrations** — introduce Alembic:

   ```powershell
   uv add alembic
   cd backend && uv run alembic init alembic
   # env.py: import app.models to populate metadata; target_metadata = Base.metadata
   uv run alembic revision --autogenerate -m "baseline"
   uv run alembic upgrade head
   ```

   Then change the runtime command to run `alembic upgrade head` before uvicorn
   instead of raw `create_all`.
5. **Vector RAG** — switch `RAG_MODE=qdrant`, provide `QDRANT_URL`; replace the
   TF retriever scoring with embeddings (keep the `GroundingContext` contract).
6. **Network** — reverse proxy (TLS), restrict `CORS_ORIGINS`, run the stack
   behind a gateway (e.g. Azure App Gateway). Consider rate limiting on
   `/executions` and `/workflows/*/run` since they spend model tokens.
7. **Observability** — export uvicorn access logs, integrate Application
   Insights / Prometheus; the audit log gives you an out-of-the-box trail.
8. **Encryption at rest** — DB-level for PostgreSQL; key management for secrets.

---

## 9. CI/CD suggestions

A minimal pipeline (GitHub Actions or Azure DevOps):

```
lint     : cd backend && uv run ruff check app tests
test     : cd backend && uv run pytest -q
build    : cd frontend && npm ci && npm run build
compose  : docker compose build
deploy   : docker compose up -d (Docker host)  /  azd up (Azure App Service + PG)
```

Frontend `VITE_API_URL` must be baked at build time with the correct public
backend origin; the backend `CORS_ORIGINS` must include that origin.

---

## 10. Common implementation gotchas

| Symptom | Cause / fix |
|---------|-------------|
| `[Errno 10048]` on boot | Port 8000 already in use — `Stop-Process` the owner or use `--port 8005` + `VITE_PROXY_TARGET` |
| "Seed already present, skipping" but data missing | DB half-seeded or schema changed — delete `prompthub.db` and restart |
| SQLite file locked on `Remove-Item` | A uvicorn process still holds it — kill it before deleting |
| Prompts created at runtime collide with seeded IDs | Counter not advanced — run seed once; seed advances the counter past 68 |
| Workflow never finishes | Real Ollama ~60 s/step — set `LLM_PROVIDER=mock` for demos |
| Frontend API calls 404 in Docker | Wrong `VITE_API_URL` baked at build (`http://host:8000/api/v1`, not `/api`) |
| CORS errors in production | Add your frontend origin to `CORS_ORIGINS` |
| 403 on admin/governance routes | Role missing — demo user `henry` is ADMIN; policy create needs GOVERNANCE or ADMIN |
| Quality score looks static | Intended — deterministic rubric (§8 TECH_GUIDE). It never changes for identical input |
| After editing DDL nothing changes | Runtime uses `create_all` (no migrations) — rebuild the DB or add Alembic |

---

**Order of reading:** `README.md` (overview) → `USERGUIDE.md` (usage) →
`TECHNICAL_GUIDE.md` (architecture) → `IMPLEMENTATION_GUIDE.md` (this file, how
to build on it).
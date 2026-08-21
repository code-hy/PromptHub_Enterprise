# PromptHub Enterprise

Self-hosted enterprise AI prompt library, engineering, testing and governance
platform. FastAPI backend + React/TypeScript frontend, seeded with a realistic
Contoso M365 demo dataset.

## What's inside

| Area        | Details |
|-------------|---------|
| **Library** | 68 seeded prompts across business functions, tasks and applications with filtering, sorting, pagination, favourites, ratings and lifecycle (draft → review → publish → deprecate/retire). |
| **Builder** | Structured prompt authoring: goal/context/source/expectations, inputs with `{placeholders}`, tone, output format, temperature, tags and governance attributes. |
| **Assistant** | Deterministic 100-point, 9-component quality rubric — `analyse`, `improve`, `generate`, `explain` modes (no LLM required). |
| **Testing** | Run prompts mock/real LLM, with optional RAG grounding over 16 synthetic Contoso M365 documents; per-run eval metrics recorded. |
| **Workflows** | Chain prompts into repeatable promptbooks (5 seeded workflows) and execute them step by step. |
| **Governance** | Policy rules engine (5 seeded policies), classification & risk posture, evaluation sandbox, security scanning, compliance violations. |
| **Analytics** | Execution volume, success rate, ratings, time saved, daily trend, top prompts and category breakdown. |
| **Audit** | Immutable `audit_events` log for every mutation. |

## Documentation

- **[WALKTHROUGH.md](WALKTHROUGH.md)** — detailed explainer for non-technical
  readers: what the app does, how every technology works (React, FastAPI,
  SQLAlchemy, LLMs, RAG, quality engine, governance), with examples.
- **[DEMO.md](DEMO.md)** — guided demo runbook: boot → explore → build → test →
  govern → run, with the exact actions and expected results.
- **[USERGUIDE.md](USERGUIDE.md)** — end-user guide: setup, configuration, every
  screen, and step-by-step scenarios.
- **[TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)** — architecture: the technology
  stack, how each component fits the scheme of things, and data-flow walkthroughs.
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** — developer guide: how to
  build, run, test, extend and production-harden the platform.

## Quick start

### Backend only (zero external services)

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8010
```

- API docs: http://localhost:8010/docs
- First boot seeds `../prompthub.db` (SQLite) automatically.
- Default `LLM_PROVIDER=auto`: uses a local Ollama if reachable, otherwise a
  fast deterministic mock. Set `LLM_PROVIDER=mock` to always skip Ollama.

### Full stack (backend + frontend)

Terminal 1:

```bash
cd backend
uv run uvicorn app.main:app --port 8010
```

Terminal 2:

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxies /api to :8010)
```

### Docker stack

```bash
docker compose up --build   # postgres, qdrant, ollama, backend, frontend
```

## Configuration (backend)

| Variable              | Default              | Notes                             |
|-----------------------|----------------------|-----------------------------------|
| `DATABASE_URL`        | *(empty → SQLite)*   | `postgresql+psycopg://…` for PG   |
| `LLM_PROVIDER`        | `auto`               | `mock` `ollama` `openai` `litellm`|
| `OLLAMA_BASE_URL`     | `http://localhost:11434` |                              |
| `OLLAMA_MODEL`        | `qwen3:1.7b`         |                                   |
| `ENABLE_AUTH`         | `false`              | demo user `henry` (ADMIN)         |
| `SEED_DEMO_DATA`      | `true`               |                                   |

## Tests

```bash
cd backend
uv run pytest tests         # 23 tests: quality rubric + API integration
uv run ruff check app tests
```

## Repository layout

```
backend/
  app/
    api/           FastAPI routers (prompts, workflows, governance, analytics…)
    models/        SQLAlchemy entities (DDL contract)
    quality/       Deterministic quality engine
    rag/           Local retriever for the Contoso M365 corpus
    services/      Domain logic
    seed/          Demo dataset (68 prompts, 5 workflows, policies, docs, analytics)
    schemas/       Pydantic request/response models
  tests/           pytest suite
frontend/
  src/
    api/           Typed API client + tanstack-query hooks
    pages/         Dashboard, Library, Detail, Builder, Assistant, Workflows,
                   Analytics, Governance, Audit, Admin
    components/    Layout + shared UI
docker-compose.yml  postgres + qdrant + ollama + backend + frontend
```
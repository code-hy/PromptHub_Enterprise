# PromptHub Enterprise — Backend

FastAPI backend for a stand-alone enterprise AI prompt library, engineering,
testing and governance platform.

## Stack

- **FastAPI** + Pydantic v2 — REST API
- **SQLAlchemy 2.0** — models (`app/models/entities.py` is the DDL contract)
  - default **SQLite** (zero setup) or **PostgreSQL** via `DATABASE_URL`
- **LLM layer** (`app/llm/`) — `mock` (deterministic, default), `ollama`
  (local), `litellm` / `openai` compatible gateways. `auto` picks Ollama when
  reachable, otherwise falls back to mock.
- **RAG** (`app/rag/`) — local keyword retrieval over the synthetic Contoso M365
  corpus; Qdrant hooks in `RAG_MODE=qdrant`.
- **Deterministic quality engine** (`app/quality/`) — 100-point, nine-component
  rubric (Goal/Context/Source/Expectations/Specificity/Constraints/Audience/
  Output format/Examples). No LLM required for scores.
- **Governance** (`app/services/governance_service.py`) — policy rules engine,
  injection/sensitive-data scanning, approval workflow.
- **Audit** — every mutation writes an `audit_events` row.

## Run locally (zero external services)

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8010
```

Open http://localhost:8010/docs for the interactive API. On first boot the
lifespan seeds the demo dataset (68 prompts, 5 workflows, governance policies,
synthetic M365 documents, analytics history) into `../prompthub.db`.

## Configuration

| Variable              | Default              | Notes                            |
|-----------------------|----------------------|----------------------------------|
| `DATABASE_URL`        | *(empty → SQLite)*   | `postgresql+psycopg://…` for PG |
| `LLM_PROVIDER`        | `auto`               | `mock` `ollama` `openai` `litellm` |
| `OLLAMA_BASE_URL`     | `http://localhost:11434` |                          |
| `OLLAMA_MODEL`        | `qwen3:1.7b`         |                                  |
| `ENABLE_AUTH`         | `false`              | demo user "henry" (GOVERNANCE)   |
| `SEED_DEMO_DATA`      | `true`               |                                  |
| `SECRET_KEY`          | dev default          | set a real secret in production |

## Tests

```bash
uv run pytest tests          # 23 tests: quality rubric + API integration
uv run ruff check app tests
```

## Docker

```bash
docker compose up --build   # postgres + qdrant + ollama + backend + frontend
```

The backend image runs the seed on start and serves the API on port 8010 on the host (container-internal port stays 8000).
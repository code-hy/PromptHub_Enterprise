# TESTING.md — PromptHub Enterprise

## Layout

```
backend/tests/
  conftest.py               # shared fixtures (temp DB, mock LLM, TestClient)
  unit/test_quality_engine.py      # deterministic rubric — no DB/HTTP
  integration/test_api.py          # full stack via TestClient (catalog, prompts, assistant, executions, workflows, governance, analytics, audit, knowledge)

frontend/
  src/lib/format.test.ts           # Vitest unit (format helpers)
  src/api/client.test.ts           # Vitest unit (typed client)
```

## Backend

```bash
cd backend
uv run ruff check app tests          # lint
uv run pytest -q                     # all 23 tests
uv run pytest tests/unit -q          # unit only (rubric)
uv run pytest tests/integration -q   # integration only (API + DB)
```

`integration/test_api.py` covers the seeded demo DB (68 prompts, 5 workflows, 5 policies, 16 docs) and the full request→service→DB→audit chain. `unit/test_quality_engine.py` covers the 9-component 100-point rubric boundaries.

CI (`.github/workflows/ci.yml`) runs both jobs: backend `pytest -q` + frontend `npm run build` (+ `npm test` once Vitest is wired). The `openapi.yaml` drift check ensures the contract file stays in sync.

## Frontend

```bash
cd frontend
npm install
npm test          # vitest run — format + client helpers
npm run build     # tsc -b + vite build
```

Frontend tests are Vitest + jsdom (see `vitest.config.ts`). They cover pure helpers (`format.ts`) and the centralized API client (`src/api/client.ts`), with instructions to run them locally and in CI.

## Manual verification

After `docker compose up --build` or local `uvicorn --port 8010` + `npm run dev`:

- `curl http://127.0.0.1:8010/health` → `{"status":"ok"}`
- `curl http://127.0.0.1:8010/api/v1/catalog` → `business_functions` + `models` (gemma4:e2b first)
- Library filters, prompt detail → Run (auto/mock/ollama), workflow 6-step run, governance badges.

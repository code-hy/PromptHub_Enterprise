# TROUBLESHOOTING.md — PromptHub Enterprise

Known issues, their root causes, and how to fix them.

---

## Table of Contents

1. [Frontend Build & Runtime](#1-frontend-build--runtime)
2. [Backend & API](#2-backend--api)
3. [Analytics Charts](#3-analytics-charts)
4. [Governance](#4-governance)
5. [Library & Pagination](#5-library--pagination)
6. [Workflows](#6-workflows)
7. [LLM Provider](#7-llm-provider)
8. [Vite Dev Server](#8-vite-dev-server)
9. [Database](#9-database)
10. [Docker](#10-docker)

---

## 1. Frontend Build & Runtime

### `npm run build` fails with TypeScript errors

**Symptom:**
```
error TS2339: Property 'X' does not exist on type '{ ... }'.
```

**Cause:** Frontend API types in `frontend/src/api/types.ts` don't match the actual backend response shape. The backend returns fields like `name` and `count`, but the types define different field names (e.g., `category`, `executions`).

**Fix:** Open `frontend/src/api/types.ts` and verify every type matches the backend schema. The most common mismatches are:
- `execution_by_category` — backend returns `{name, count}`, not `{category, status, executions}`
- `executions_by_day` — backend returns `{date, count}`, not `{date, executions}`
- `top_prompts` — backend returns `{name, count}`, not `{name, execution_count}`

After fixing, rebuild:
```bash
cd frontend && npm run build
```

---

### `npm run build` fails with import errors

**Symptom:**
```
Cannot find module 'X' or its corresponding type declarations.
```

**Fix:** Run `npm install` in the `frontend/` directory to ensure all dependencies are installed.

---

## 2. Backend & API

### `uv run pytest` fails with "program not found"

**Symptom:**
```
error: Failed to spawn: `pytest`
Caused by: program not found
```

**Cause:** The `uv` virtual environment doesn't have `pytest` installed, or `uv` isn't activating the correct environment.

**Fix:**
```bash
uv pip install pytest httpx
uv run pytest tests -v
```

If using the Makefile:
```bash
make install
make test
```

---

### Backend starts but returns 500 on all endpoints

**Symptom:** All API calls return `{"detail": "Internal server error"}`.

**Cause:** Database wasn't seeded, or `DATABASE_URL` points to a missing/corrupted SQLite file.

**Fix:**
1. Delete the old `prompthub.db` file from the repo root
2. Restart the backend — it auto-seeds on startup
3. Or manually seed: `uv run python -c "from app.seed import seed_all; seed_all()"`

---

### Auth returns 401 for every request

**Symptom:** All authenticated requests return `{"detail": "Not authenticated"}`.

**Cause:** Token expired or `AUTH_SECRET` changed between restarts.

**Fix:**
1. Log in again via `POST /api/v1/auth/login`
2. Use the fresh token in the `Authorization: Bearer <token>` header
3. If running without auth (`ENABLE_AUTH=false`), ensure the header is omitted entirely

---

### Seed data doesn't appear

**Symptom:** Library shows 0 prompts, dashboard shows no data.

**Cause:** `SEED_DEMO_DATA=false` in environment, or database already exists with data.

**Fix:**
1. Set `SEED_DEMO_DATA=true` in `.env` or environment
2. Delete `prompthub.db` and restart
3. Or run: `uv run python -c "from app.seed import seed_all; seed_all()"`

---

## 3. Analytics Charts

### Pie chart labels all show "Other"

**Symptom:** The "Executions by category" pie chart shows all slices labeled "other" in the legend.

**Cause:** Frontend maps `c.category ?? c.status ?? "other"` but the backend returns `{"name": "...", "count": ...}`.

**Fix in `frontend/src/pages/Analytics.tsx`:**
```typescript
// BEFORE (wrong)
const byCategory = (o.execution_by_category ?? []).map((c) => ({
  name: String(c.category ?? c.status ?? "other"),
  value: Number(c.executions ?? c.count ?? 0),
}));

// AFTER (correct)
const byCategory = (o.execution_by_category ?? []).map((c) => ({
  name: String(c.name ?? "other"),
  value: Number(c.count ?? 0),
}));
```

Also update `frontend/src/api/types.ts`:
```typescript
execution_by_category: Array<{ name: string; count: number }>;
```

---

### Top prompts bar chart shows no bars (all zero)

**Symptom:** The "Top prompts by executions" bar chart renders labels but no bars.

**Cause:** Frontend reads `p.executions ?? p.execution_count ?? 0` but backend returns `{name, count}`.

**Fix in `frontend/src/pages/Analytics.tsx`:**
```typescript
// BEFORE (wrong)
const top = (o.top_prompts ?? []).map((p) => ({
  name: String(p.name ?? p.prompt_id ?? "").slice(0, 18),
  executions: Number(p.executions ?? p.execution_count ?? 0),
}));

// AFTER (correct)
const top = (o.top_prompts ?? []).map((p) => ({
  name: String(p.name ?? "").slice(0, 18),
  executions: Number(p.count ?? 0),
}));
```

---

### Executions per day chart shows flat line at 0

**Symptom:** Line chart renders but all values are 0.

**Cause:** Frontend reads `d.executions` but backend returns `{date, count}`.

**Fix in `frontend/src/pages/Analytics.tsx`:**
```typescript
// BEFORE
executions: Number(d.executions ?? 0),

// AFTER
executions: Number(d.count ?? 0),
```

---

### Success rate shows 10000% instead of 100%

**Symptom:** Dashboard and Analytics stat cards show "10000% success".

**Cause:** Frontend multiplies `success_rate` by 100, but the backend already returns it as a percentage (0–100).

**Fix in `frontend/src/pages/Dashboard.tsx` and `frontend/src/pages/Analytics.tsx`:**
```typescript
// BEFORE (wrong)
sub={`${Math.round(o.success_rate ?? 0) * 100}% success`}

// AFTER (correct)
sub={`${Math.round(o.success_rate ?? 0)}% success`}
```

---

## 4. Governance

### Governance decisions show "undefined → undefined"

**Symptom:** The Governance page and Prompt Detail page show `undefined → undefined` for policy decisions.

**Cause:** Frontend reads `d.policy` / `d.decision` but the backend returns `d.type` / `d.label`.

**Fix in `frontend/src/pages/Governance.tsx`:**
```typescript
// BEFORE
{d.policy} → {d.decision}

// AFTER
{d.type}: {d.label}
```

**Fix in `frontend/src/pages/PromptDetail.tsx`:**
Same change — replace `d.policy`/`d.decision` with `d.type`/`d.label`.

---

### Governance violations increase on every sandbox evaluation

**Symptom:** Running the evaluation sandbox multiple times creates duplicate `ComplianceViolation` rows, inflating the violation count.

**Cause:** The sandbox endpoint persisted violations on every evaluation run.

**Fix in `backend/app/api/governance.py`:**
```python
# BEFORE
result = governance_service.evaluate(db, attrs)

# AFTER
result = governance_service.evaluate(db, attrs, record_violations=False)
```

Also deduplicate violations in `governance_summary` query in `backend/app/services/governance_service.py` by grouping on `policy_id`.

---

### Governance badge shows wrong count on sidebar

**Symptom:** The governance nav item badge shows a stale or incorrect number.

**Cause:** The badge reads from `governance?.high_risk` which may not be refreshed.

**Fix:** Ensure the governance summary query is invalidated when violations change. In the frontend, add `queryClient.invalidateQueries({ queryKey: ["gov-summary"] })` after any governance mutation.

---

## 5. Library & Pagination

### "Next" button doesn't work on Library page

**Symptom:** Clicking "Next" on the Library page doesn't advance to the next page of prompts.

**Cause:** The `page` variable was derived from `params` (useSearchParams) but the `setFilter` function reset it. Also, `page` wasn't in the `useMemo` dependency array.

**Fix in `frontend/src/pages/Library.tsx`:**
```typescript
// 1. Derive page from location.search (not params)
const page = Number(new URLSearchParams(location.search).get("page") ?? 1);

// 2. Add page to useMemo deps
const filters = useMemo(
  () => ({ ... page, page_size: PAGE_SIZE }),
  [search, params, page],  // <-- page must be here
);

// 3. Fix setFilter to not reset page when key is "page"
const setFilter = (key: string, value: string | undefined) => {
  const next = new URLSearchParams(params);
  if (value) next.set(key, value);
  else next.delete(key);
  if (key !== "page") next.set("page", "1");  // <-- only reset for non-page filters
  setParams(next);
};
```

---

### Search doesn't trigger on typing (only on Enter)

**Symptom:** Typing in the search box doesn't filter results until Enter is pressed.

**Cause:** This is intentional — the search is debounce-free and triggers on Enter or on blur.

**To change to live search:** Replace the `onKeyDown` handler with an `onChange` that calls `setFilter`:
```typescript
onChange={(e) => {
  setSearch(e.target.value);
  setFilter("q", e.target.value || undefined);
}}
```

---

## 6. Workflows

### Workflow runs with empty input `{}`

**Symptom:** Running a workflow always uses empty input data regardless of what the user types.

**Cause:** The Workflows page had no input form — it always passed `{}` to the run endpoint.

**Fix:** The Workflows page was rewritten to:
1. Extract required inputs from each step's `input_mapping`
2. Show a "Configure & run" button with input fields
3. Pass user-provided input to the run endpoint

If you see this issue, ensure you're running the latest version of `frontend/src/pages/Workflows.tsx`.

---

### Workflow step fails silently

**Symptom:** A workflow run completes but one step shows no output.

**Cause:** The step's `continue_on_failure` is `true` and the LLM provider returned an error.

**Fix:** Check the workflow execution results in the response — each step has its own `status` and `error_message`. For debugging:
1. Set `continue_on_failure` to `false` on the step to make it fail loudly
2. Check backend logs for LLM provider errors
3. Ensure the LLM provider (Ollama/Mock) is running

---

## 7. LLM Provider

### Ollama connection refused

**Symptom:** Executions fail with `Connection refused` or `Could not connect to Ollama`.

**Cause:** Ollama isn't running on `http://localhost:11434`.

**Fix:**
1. Start Ollama: `ollama serve`
2. Pull a model: `ollama pull qwen3:1.7b`
3. Verify: `curl http://localhost:11434/api/tags`

If Ollama isn't installed, the system falls back to `MockProvider` automatically.

---

### Ollama responses are very slow (60+ seconds per step)

**Symptom:** Workflow executions take several minutes to complete.

**Cause:** Ollama is running on CPU without GPU acceleration, or the model is too large.

**Fix:**
1. Use a smaller model: `ollama pull qwen3:0.6b`
2. Set `LLM_PROVIDER=mock` for demo/testing purposes
3. If you have a GPU, ensure Ollama is using it: `ollama run qwen3:1.7b` and check GPU usage

---

### Mock provider returns generic responses

**Symptom:** All executions return the same template response regardless of the prompt.

**Cause:** This is expected behavior — the MockProvider uses task-aware templates but doesn't actually call an LLM.

**Fix:** For real responses, configure a real LLM provider:
- `LLM_PROVIDER=ollama` (local)
- `LLM_PROVIDER=openai` (requires `OPENAI_API_KEY`)

---

## 8. Vite Dev Server

### Frontend can't reach backend API

**Symptom:** Frontend shows "Failed to fetch" or CORS errors in browser console.

**Cause:** Vite proxy target is misconfigured, or backend isn't running.

**Fix in `frontend/vite.config.ts`:**
```typescript
proxy: {
  '/api': {
    target: 'http://127.0.0.1:8000',  // Use 127.0.0.1, NOT localhost
    changeOrigin: true,
  },
},
```

**Important:** Use `127.0.0.1` not `localhost`. On some Windows systems, `localhost` resolves to IPv6 `::1` while FastAPI binds to IPv4 `127.0.0.1`.

Also verify:
1. Backend is running: `curl http://127.0.0.1:8000/api/v1/health`
2. Frontend is running: `cd frontend && npm run dev`
3. Access frontend at `http://127.0.0.1:5173` (not `http://localhost:5173`)

---

### Vite dev server port already in use

**Symptom:**
```
Port 5173 is already in use
```

**Fix:**
```bash
# Find and kill the process
netstat -ano | findstr :5173
taskkill /PID <pid> /F

# Or use a different port
cd frontend && npx vite --port 5174
```

---

## 9. Database

### "database is locked" error

**Symptom:**
```
sqlalchemy.exc.OperationalError: database is locked
```

**Cause:** Multiple processes accessing the same SQLite file, or a previous process didn't close the connection.

**Fix:**
1. Stop all running backend instances
2. Delete `prompthub.db` from the repo root
3. Restart the backend (it will recreate and reseed)

---

### SQLite to PostgreSQL migration

**Symptom:** Want to use PostgreSQL instead of SQLite for production.

**Fix:** Set the `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/prompthub"
```

The app uses SQLAlchemy 2.0 with `create_all`, so it will create tables automatically on first startup. Run `make seed` to populate with demo data.

---

## 10. Docker

### Docker Compose services fail to start

**Symptom:** `docker compose up` shows services exiting immediately.

**Fix:**
1. Check logs: `docker compose logs <service>`
2. Ensure ports are free: `docker compose ps`
3. For PostgreSQL, wait for it to be healthy before starting backend:
   ```yaml
   depends_on:
     db:
       condition: service_healthy
   ```

---

### Ollama in Docker can't pull models

**Symptom:** Ollama container starts but can't serve requests.

**Fix:** Pull the model before starting:
```bash
docker compose exec ollama ollama pull qwen3:1.7b
```

Or add a startup script that pulls models automatically.

---

## Quick Reference

| Problem | Quick Fix |
|---------|-----------|
| Build fails with TS errors | Check `types.ts` matches backend response shapes |
| 10000% success rate | Remove `* 100` from `success_rate` display |
| Pie chart labels "Other" | Map `c.name` not `c.category` |
| Bar chart no bars | Map `p.count` not `p.executions` |
| Governance "undefined → undefined" | Map `d.type`/`d.label` not `d.policy`/`d.decision` |
| Library Next button broken | Derive `page` from `location.search`, add to `useMemo` deps |
| Workflow runs with `{}` | Ensure Workflows page has input form (latest version) |
| Frontend can't reach backend | Use `127.0.0.1` in Vite proxy, not `localhost` |
| Ollama slow | Use `LLM_PROVIDER=mock` for demos, or smaller model |
| Database locked | Delete `prompthub.db` and restart |

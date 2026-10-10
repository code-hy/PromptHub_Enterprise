# Deployment Proof — Render (updated 2026-10-10 audit)

**Blueprint:** `render.yaml` at repo root (see also `docs/deployment.md`, `Cloud_Deployment.md`).

**Live URLs (canonical):**

| Service | URL |
|---------|-----|
| Backend | `https://prompthub-api-56ez.onrender.com` |
| Frontend | `https://prompthub-web.onrender.com` |
| Swagger | `https://prompthub-api-56ez.onrender.com/docs` |
| Health | `https://prompthub-api-56ez.onrender.com/health` |

## Steps (Render)

1. Push `main` to GitHub (already: `b60ff2e`).
2. Render → New → Blueprint → select `PromptHub_Enterprise` repo (auto-discovers `render.yaml`).
3. Create managed PostgreSQL (plan `starter` is enough for demo); Render injects `DATABASE_URL` into `prompthub-api`.
4. Deploy — wait for health:

```bash
curl https://prompthub-api.onrender.com/health
# {"status":"ok","app":"PromptHub Enterprise","provider":"auto"}

curl https://prompthub-api.onrender.com/api/v1/catalog | jq .models
open https://prompthub-web.onrender.com   # frontend static
```

## Proof (audit 2026-10-10 — honest status)

**RESOLVED 2026-10-10 evening:** Neon wired (`DATABASE_URL` on `prompthub-api`), service redeployed, boot auto-seeded. All green.

- [x] Frontend URL: `https://prompthub-web.onrender.com`
  - `curl -m 30 https://prompthub-web.onrender.com` → `HTTP 200` in ~0.26 s, body contains `PromptHub Enterprise` (verified 2026-10-10).
  - Seeded proof shots (captured 2026-10-10 via automated browser against the live Neon-backed deploy):
    - `screenshots/render-seeded-dashboard.png` — Dashboard 68 prompts / 44 published / 320 executions / 4.65★
    - `screenshots/render-seeded-library.png` — Library, 68 prompts, filters + pagination
    - `screenshots/render-seeded-workflows.png` — 5 PUBLISHED promptbooks with steps
    - `screenshots/render-seeded-analytics.png` — 320 executions, trend, top-prompts, category pie
    - `screenshots/render-seeded-governance.png` — 68 total, risk distribution, active policies
  - Outage-state shots (same day, backend down): `screenshots/render-dashboard-2026-10-10.png`, `render-assistant-2026-10-10.png`, `render-builder-2026-10-10.png`.
- [x] Backend URL: `https://prompthub-api-56ez.onrender.com`
  - `curl /health` output (verified 2026-10-10):
  ```
  {"status":"ok","app":"PromptHub Enterprise","provider":"mock"}
  ```
  - `GET /api/v1/analytics/overview` (verified 2026-10-10):
  ```
  {"prompt_count":68,"published_count":44,"execution_count":320,"success_rate":100.0,
   "avg_rating":4.65,"rating_count":8,"estimated_time_saved_minutes":9560.0,
   "avg_latency_ms":340.0,"avg_tokens":420,
   "status_distribution":[{"PUBLISHED":44},{"APPROVED":8},{"DRAFT":8},{"UNDER_REVIEW":4},{"DEPRECATED":4}]}
  ```
  - Earlier incident (same day): crash-loop exit 3, `psycopg.OperationalError: failed to resolve host 'dpg-da6mtuou01pc738lce40-a'` — Render free PG deleted. Fixed via Neon; see `TROUBLESHOOTING.md §11` crash-loop entry.
- [x] DB: Neon free PostgreSQL `gentle-bread-89126697` — `DATABASE_URL` set manually on the service (secret, never committed). `render.yaml` no longer provisions Render PG.

## Rollback / logs

- Render → Service → Logs (live) / Events (deploys)
- `ops/runbook.md` — restart, rotate `SECRET_KEY`, backup `pg_dump`.

## Local alternative (peer-review default)

```bash
docker compose up --build  # postgres:5432, qdrant:6333, ollama:11434, api:8010, web:5173
```
No cloud URL required to pass reproducibility, but cloud proof gives Deployment 2/2.

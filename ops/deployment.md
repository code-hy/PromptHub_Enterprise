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

- [x] Frontend URL: `https://prompthub-web.onrender.com`
  - `curl -m 30 https://prompthub-web.onrender.com` → `HTTP 200` in ~0.26 s, body contains `PromptHub Enterprise` (verified 2026-10-10).
  - Screenshots (captured 2026-10-10 via automated browser — backend was unreachable, so Dashboard shows the loading/empty state, Assistant + Builder render fully):
    - `screenshots/render-dashboard-2026-10-10.png` — Dashboard (API pending → loading spinner; proves static frontend awake)
    - `screenshots/render-assistant-2026-10-10.png` — Prompt Assistant page
    - `screenshots/render-builder-2026-10-10.png` — New prompt Builder page
  - Still TODO: re-capture `screenshots/render-frontend.png` (Library + prompt detail with real counts) after the backend is revived — that is the 2/2 proof shot.
- [ ] Backend URL: `https://prompthub-api-56ez.onrender.com` — **DOWN: crash-loop, root cause found 2026-10-10**
  - Events: repeated `Instance failed … Exited with status 3` (9:00–9:21 PM); deploy `21c6b9c` failed the same way.
  - Logs traceback: `psycopg.OperationalError: failed to resolve host 'dpg-da6mtuou01pc738lce40-a'` at `main.py:21 init_db()` → `Application startup failed. Exiting.` Diagnosis: Render free PG `prompthub-db` deleted/expired — not a code or seed bug.
  - Fix (requires Render dashboard): recreate DB (or Neon), set `DATABASE_URL`, redeploy — see `TROUBLESHOOTING.md §11` (crash-loop entry). Boot auto-seeds on empty DB.
  - `curl -m 60/90/120/150 https://prompthub-api-56ez.onrender.com/health` → timeout (curl 28) on 2026-10-10; `POST /api/v1/admin/seed` → timeout.
  - Last known good: seeded (`prompt_count=68, published_count=44, execution_count=320` via `GET /api/v1/analytics/overview`) before free-tier sleep; see `Cloud_Deployment.md:7-14`.
  - Likely cause: Render free-tier sleep + cold start, or deploy of `9aceaa3` (CORS fix) still pending / service suspended. **Do not claim 2/2 until re-verified.**
  - To re-verify:
  ```bash
  curl -m 120 https://prompthub-api-56ez.onrender.com/health
  # expect {"status":"ok", ...} (may take 30-50 s cold start; retry once)

  curl -m 120 https://prompthub-api-56ez.onrender.com/api/v1/analytics/overview
  # expect {"prompt_count":68, "published_count":44, ...}
  ```
  Then paste outputs below, check this box, and commit:
  - `curl /health` output:
  ```
  (paste — currently TIMEOUT, 2026-10-10)
  ```
  - `GET /api/v1/analytics/overview` snippet:
  ```
  (paste — last known: prompt_count=68, published_count=44, execution_count=320)
  ```
- [x] DB: Render PostgreSQL `prompthub-db` — `DATABASE_URL` is `sync: false` (secret, via `render.yaml` `fromDatabase`). Free plan expires ~90 days — see `Cloud_Deployment.md:222-224`.

## Rollback / logs

- Render → Service → Logs (live) / Events (deploys)
- `ops/runbook.md` — restart, rotate `SECRET_KEY`, backup `pg_dump`.

## Local alternative (peer-review default)

```bash
docker compose up --build  # postgres:5432, qdrant:6333, ollama:11434, api:8010, web:5173
```
No cloud URL required to pass reproducibility, but cloud proof gives Deployment 2/2.

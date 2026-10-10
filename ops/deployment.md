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
  - Screenshot: `screenshots/render-frontend.png` — **TODO: capture Library + prompt detail and save under that path** (folder currently has local-only PNGs).
- [ ] Backend URL: `https://prompthub-api-56ez.onrender.com` — **DOWN at audit time**
  - `curl -m 60/90 https://prompthub-api-56ez.onrender.com/health` → timeout after 60 s and 90 s (curl exit 28) on 2026-10-10; `webfetch /health` → 503 earlier same day.
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

# Deployment Proof — Render (fill after deploy)

**Blueprint:** `render.yaml` at repo root (see also `docs/deployment.md`).

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

## Proof (paste after deploy)

- [ ] Backend URL: `https://______________.onrender.com`
  - `curl /health` output:
  ```
  (paste)
  ```
  - `GET /api/v1/catalog` snippet:
  ```
  (paste)
  ```
- [ ] Frontend URL: `https://______________.onrender.com`
  - Screenshot: `screenshots/render-frontend.png` (library + prompt detail with gemma4:e2b)
- [ ] DB: Render PostgreSQL `prompthub-db` — `DATABASE_URL` is `sync: false` (secret)

## Rollback / logs

- Render → Service → Logs (live) / Events (deploys)
- `ops/runbook.md` — restart, rotate `SECRET_KEY`, backup `pg_dump`.

## Local alternative (peer-review default)

```bash
docker compose up --build  # postgres:5432, qdrant:6333, ollama:11434, api:8010, web:5173
```
No cloud URL required to pass reproducibility, but cloud proof gives Deployment 2/2.

# Deployment — Render (and alternatives)

## Render blueprint

This repo includes `render.yaml` (see repo root) and `ops/render.md` with the full
Render steps. The TL;DR for a fresh Render project:

1. Create a Render account and connect the `PromptHub_Enterprise` GitHub repo.
2. Create a **PostgreSQL** managed instance (Render → New → PostgreSQL).
3. Apply the blueprint **or** create two Web Services:
   - **Backend** — Docker `backend/Dockerfile`, env `DATABASE_URL=<render postgres URL>`, `LLM_PROVIDER=mock` (or `ollama` if you add an Ollama private service), health check `/health`.
   - **Frontend** — Docker `frontend/Dockerfile` or Static Site (`npm run build` → `dist/`), env `VITE_API_URL=https://<backend>.onrender.com/api/v1`.
4. After deploy, verify `https://<backend>/health` → `{"status":"ok"}` and `GET /api/v1/catalog`.

Copy the live URLs into `ops/deployment.md` as proof (screenshots or `curl` output).

## Local / Docker (still the default for peer review)

```bash
docker compose up --build # postgres + qdrant + ollama + backend:8010 + frontend:5173
```

## CI-driven deploy hook (active)

`.github/workflows/ci.yml` `docker` job (gated on `main` push, after backend+frontend pass): `docker compose config -q && docker compose build`, Trivy fs scan (HIGH/CRITICAL, non-blocking), then `POST $RENDER_DEPLOY_HOOK` on success — gracefully skips with a notice if the `RENDER_DEPLOY_HOOK` secret is unset (Render auto-deploys on push when auto-deploy is ON).

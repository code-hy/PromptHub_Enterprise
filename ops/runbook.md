# Runbook — Day-2 Ops

## Start / stop
```bash
# local
cd backend && uv run uvicorn app.main:app --reload --port 8010
cd frontend && npm run dev
# or
docker compose up --build -d
docker compose logs -f backend frontend
```

## Logs & health
- `GET /health` → `{"status":"ok"}`
- `audit_events` is immutable; governance violations in `compliance_violations`.

## Backup
```bash
# SQLite dev
copy prompthub.db prompthub.db.bak
# Postgres (Render / compose)
pg_dump "$DATABASE_URL" > dump.sql
```

## Rotate secrets
- `SECRET_KEY` in `backend/.env` or Render env — restart backend after change.
- `OPENAI_API_KEY` via Render `sync: false`.

## Ollama models
```bash
ollama list              # should show gemma4:e2b
OLLAMA_MODEL=gemma4:e2b uv run uvicorn app.main:app --port 8010
```

## Incident: port squatting (see TROUBLESHOOTING.md)
- `Get-NetTCPConnection -LocalPort 8010 -State Listen` → `docker ps`
- `render.yaml` pins backend host to `:10000` internally but exposes via Render routing; local dev uses `:8010` to avoid WSL/Docker conflicts.

## Scaling notes
- Frontend is static (`npm run build` → `dist/`); scale backend horizontally when `POST /api/v1/executions` p95 > 2s.
- Qdrant is optional (`RAG_MODE=local` is the zero-deps default).

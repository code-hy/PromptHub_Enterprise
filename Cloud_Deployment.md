# Cloud Deployment — Render Free-tier

Complete guide for deploying PromptHub Enterprise to Render free-tier.

---

## Live deployment

| Service | URL | Status |
|---------|-----|--------|
| **Frontend** | https://prompthub-web.onrender.com | Live |
| **Backend API** | https://prompthub-api-56ez.onrender.com | Live, seeded (68 prompts) |
| Swagger docs | https://prompthub-api-56ez.onrender.com/docs | Auto-generated |
| Health check | https://prompthub-api-56ez.onrender.com/health | `{"status":"ok"}` |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser (prompthub-web.onrender.com)                   │
│  React SPA built with VITE_API_URL baked at build time  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS (cross-origin)
                       │ CORS: prompthub-web.onrender.com
┌──────────────────────▼──────────────────────────────────┐
│  Backend (prompthub-api-56ez.onrender.com)              │
│  FastAPI + Uvicorn on $PORT (Render sets 10000)         │
│  LLM_PROVIDER=mock, ENABLE_AUTH=false                   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  Render Free PostgreSQL (prompthub-db)                  │
│  Auto-wired via render.yaml fromDatabase                │
│  Expires ~90 days — set calendar reminder at day 80     │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- GitHub account with `PromptHub_Enterprise` repo
- Render account (free tier)

## Deploy from scratch

### 1. Database

**Option A — Render Free PostgreSQL (quickest)**

The blueprint creates this automatically. Skip to step 2.

**Option B — Neon Free (permanent, recommended)**

1. Go to https://neon.tech → New Project
2. Copy the connection string
3. On Render → `prompthub-api` → Environment → set:
   ```
   DATABASE_URL=postgresql+psycopg://user:pass@ep-xxx.us-east-2.aws.neon.cloud/prompthub
   ```
4. Delete the `databases:` block from `render.yaml` if using Neon

### 2. Backend (Web Service)

1. Render → New → Web Service → Connect `PromptHub_Enterprise` repo
2. Settings:
   - **Name:** `prompthub-api`
   - **Runtime:** Docker
   - **Dockerfile:** `./backend/Dockerfile`
   - **Docker context:** `./backend`
   - **Plan:** Free
   - **Health check path:** `/health`
3. Environment variables:
   ```
   DATABASE_URL          (from Database step, or auto-filled by blueprint)
   LLM_PROVIDER         mock
   SEED_DEMO_DATA       true
   ENABLE_AUTH          false
   SECRET_KEY           (generate a random string)
   CORS_ORIGINS         https://prompthub-web.onrender.com
   ```
4. Create service → wait for **Live** status

Verify:
```bash
curl https://prompthub-api-56ez.onrender.com/health
# {"status":"ok","app":"PromptHub Enterprise","provider":"mock"}

curl https://prompthub-api-56ez.onrender.com/api/v1/catalog
# Returns functions, tasks, statuses, models, etc.
```

### 3. Frontend (Static Site — recommended)

A Static Site is cheaper (no cold start sleep) and faster than a second Docker service.

1. Render → New → Static Site → Connect same repo
2. Settings:
   - **Name:** `prompthub-web`
   - **Build command:** `cd frontend && npm install && npm run build`
   - **Publish directory:** `frontend/dist`
   - **Plan:** Free
3. Environment variables:
   ```
   VITE_API_URL=https://prompthub-api-56ez.onrender.com/api/v1
   ```
4. Create → wait for deploy

**Alternative: Docker Web Service**

If you prefer both services as Docker (as defined in `render.yaml`):

1. Render → New → Blueprint → select `PromptHub_Enterprise` repo
2. Blueprint auto-creates `prompthub-api`, `prompthub-web`, and `prompthub-db`
3. Verify `prompthub-web` has `VITE_API_URL` baked correctly (see Troubleshooting)

### 4. Push updates

```bash
git push origin main
# Render auto-deploys (if auto-deploy is ON in service settings)
# Or trigger manually: Render → Service → Manual Deploy → Clear build cache & deploy
```

## How the Dockerfiles work

### Backend Dockerfile (`backend/Dockerfile`)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock* ./
COPY app ./app
COPY README.md ./
RUN uv sync --frozen 2>/dev/null || uv sync
EXPOSE 8000
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Key points:
- Uses `$PORT` if set (Render sets 10000), falls back to 8000 for local dev
- `EXPOSE 8000` is the default; Render overrides with `$PORT`

### Frontend Dockerfile (`frontend/Dockerfile`)

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
ARG VITE_API_URL=http://localhost:8010/api/v1
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build
EXPOSE 5173
CMD ["sh", "-c", "npm run preview -- --host 0.0.0.0 --port ${PORT:-5173}"]
```

Key points:
- `VITE_API_URL` is baked at build time via `ARG`/`ENV`
- `render.yaml` passes `buildArgs: VITE_API_URL=https://prompthub-api-56ez.onrender.com/api/v1`
- Also set as `envVars` so `import.meta.env.VITE_API_URL` works at runtime

## How CORS works on Render

The backend (`config.py:48`) has a default CORS allow list:

```python
cors_origins: str = "http://localhost:5173,http://localhost:4173,http://127.0.0.1:5173,http://127.0.0.1:4173,https://prompthub-web.onrender.com"
```

When the browser on `prompthub-web.onrender.com` calls `prompthub-api-56ez.onrender.com`, it's a cross-origin request. The browser sends a preflight `OPTIONS` request. The backend must respond with `Access-Control-Allow-Origin: https://prompthub-web.onrender.com`.

**If the frontend URL is missing from CORS_ORIGINS**, all API calls fail silently — the Dashboard shows 0 prompts, Library shows "No prompts match your filters". The browser console shows:

```
Access to fetch at 'https://prompthub-api-56ez.onrender.com/api/v1/...' from origin
'https://prompthub-web.onrender.com' has been blocked by CORS policy
```

**Fix:** Add `https://prompthub-web.onrender.com` to `CORS_ORIGINS` on the backend service, or ensure it's in the default list (it is since commit `9aceaa3`).

## How VITE_API_URL works

The frontend uses `import.meta.env.VITE_API_URL` to know where the backend is:

```typescript
// frontend/src/api/client.ts
const rawBase = (import.meta.env.VITE_API_URL as string | undefined) || "/api/v1";
```

On Render, `VITE_API_URL` is baked into the JavaScript bundle at build time. Changing it requires a re-deploy of the frontend.

**Runtime fallback** (commit `2c38edc`): If the baked URL is wrong (localhost, truncated host), the client corrects it at runtime when it detects `window.location.hostname.endsWith("onrender.com")`.

## Environment variables reference

| Variable | Service | Value | Notes |
|----------|---------|-------|-------|
| `DATABASE_URL` | Backend | `postgresql+psycopg://...` | Auto-wired from `render.yaml` `fromDatabase` |
| `LLM_PROVIDER` | Backend | `mock` | No Ollama on free-tier |
| `SEED_DEMO_DATA` | Backend | `true` | Seeds 68 prompts on first boot |
| `ENABLE_AUTH` | Backend | `false` | Skip login for demo |
| `SECRET_KEY` | Backend | *(generated)* | Used for HMAC token signing |
| `CORS_ORIGINS` | Backend | `https://prompthub-web.onrender.com` | Comma-separated allowed origins |
| `VITE_API_URL` | Frontend | `https://prompthub-api-56ez.onrender.com/api/v1` | Baked at build time |

## Free-tier limitations

| Limit | Detail |
|-------|--------|
| **Sleep** | Services sleep after 15 min inactivity |
| **Cold start** | First request after sleep: 30-50 s |
| **RAM** | 512 MB per Web Service |
| **Hours** | 750 hrs/month per service |
| **PostgreSQL** | Free plan expires ~90 days, 1 GB limit |
| **Bandwidth** | 100 GB/month (Static Site) |

### Staying under 750 hrs

One Web Service kept awake by traffic uses ~720 hrs/month. With sleep, you use less. Set a cron job or UptimeRobot to ping `/health` every 10 minutes if you need it always awake.

### PostgreSQL expiry

Free Render PostgreSQL expires after ~90 days. Set a calendar reminder at day 80 to migrate to a new database or upgrade to a paid plan.

## Troubleshooting

### Dashboard shows 0 / 0 / 0

**Cause:** CORS blocking or wrong `VITE_API_URL`.

1. Open DevTools (F12) → Network tab → refresh
2. Find `analytics/overview` request → check Request URL
3. If it's `localhost` or truncated: frontend needs re-deploy with correct `VITE_API_URL`
4. If it's correct but fails with CORS error: add `https://prompthub-web.onrender.com` to `CORS_ORIGINS` on backend

### Library shows "No prompts match your filters"

Same as above — CORS is blocking the `/prompts` API call. Check DevTools Network tab.

### Cold start is slow (30-50 s)

Normal for free-tier. The service sleeps after 15 min idle. First request wakes it up.

### Frontend shows wrong API host

The `VITE_API_URL` wasn't baked correctly. On Render:
1. Go to `prompthub-web` → Environment → verify `VITE_API_URL` is set
2. Manual Deploy → Clear build cache & deploy

### Backend logs show "Seed already present, skipping"

The database already has data. This is normal on restart — the seed is idempotent.

### Backend returns 500 on all endpoints

1. Check Render → `prompthub-api` → Logs for errors
2. Verify `DATABASE_URL` is set and points to a valid PostgreSQL database
3. If using Neon, ensure the connection string uses `+psycopg` (not `+psycopg2`)

### Port already in use

Render sets `$PORT` automatically. The Dockerfiles use `${PORT:-8000}` (backend) and `${PORT:-5173}` (frontend). This should not happen on Render.

## Manual re-seed on Render

If you need to re-seed the database on Render:

```bash
# Via Render Shell (Shell Access on the backend service):
cd /app
uv run python -c "from app.seed import seed_all; seed_all()"
```

Or use the admin API:

```bash
curl -X POST https://prompthub-api-56ez.onrender.com/api/v1/admin/seed
# Returns: {"seeded": true, "message": "Seed complete"}
```

## Rollback

1. Render → Service → Events tab → find previous successful deploy
2. Click **Rollback to this deploy**
3. Or: fix the issue on a new commit and push → Render auto-deploys

## Cost estimate

| Service | Plan | Monthly cost |
|---------|------|-------------|
| Backend (Web Service) | Free | $0 |
| Frontend (Static Site) | Free | $0 |
| PostgreSQL | Free | $0 |
| **Total** | | **$0** |

Free-tier expires: PostgreSQL at ~90 days. Web Services at 750 hrs/month.

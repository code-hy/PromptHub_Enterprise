# Render Free-tier Deploy — Step-by-step

Your free-tier plan: 750 hrs/month, sleep after 15 min, 512 MB RAM, free PG expires ~90 days.

> Full reference: see `Cloud_Deployment.md` in the repo root.

## Live deployment

| Service | URL | Status |
|---------|-----|--------|
| Frontend | https://prompthub-web.onrender.com | Live |
| Backend API | https://prompthub-api-56ez.onrender.com | Live, seeded (68 prompts) |
| DB | Render Free PostgreSQL (`prompthub-db`) | Active, expires ~90 days |

## Fastest free path (recommended: Backend Docker + Frontend Static + Neon DB)

Free-tier Blueprint above works, but for permanence do **Manual** instead of Blueprint DB:

### 1. DB (pick one)

| Option | Steps | Note |
|---|---|---|
| **A. Render Free PG** (quickest) | Let Blueprint create `prompthub-db` (`plan: free`) — auto-wires `DATABASE_URL` | Expires ~90 days, 1 GB |
| **B. Neon Free** (permanent) | https://neon.tech → New Project → copy connection string → Render → Backend → Environment → `DATABASE_URL=postgresql+psycopg://...` (use `+psycopg` not `+psycopg2`). Delete `databases:` block from `render.yaml` if using this | Free 0.5 GB, never sleeps |

### 2. Backend (Web Service, Free)

*Render → New → Web Service → Connect `PromptHub_Enterprise` repo*

- Runtime: **Docker**, Dockerfile: `backend/Dockerfile`
- Plan: **Free**, Health check: `/health`
- Env:
  ```
  LLM_PROVIDER=mock
  SEED_DEMO_DATA=true
  ENABLE_AUTH=false
  SECRET_KEY=<Generate>
  DATABASE_URL=<from DB step>  # or auto-filled from Blueprint DB
  CORS_ORIGINS=https://prompthub-web.onrender.com
  ```
- Note: Dockerfile respects `$PORT`; Render sets 10000.

Wait for `Live` → test:
```bash
curl https://prompthub-api-56ez.onrender.com/health
# {"status":"ok","app":"PromptHub Enterprise","provider":"mock"}
```

### 3. Frontend (Static Site, Free — better than Docker)

*Render → New → Static Site → Connect same repo*

- Build: `cd frontend && npm install && npm run build`
- Publish: `frontend/dist`
- Plan: **Free**
- Env:
  ```
  VITE_API_URL=https://prompthub-api-56ez.onrender.com/api/v1
  ```
- After Backend is live, **Manual Deploy → Clear build cache & Deploy** so `VITE_API_URL` bake uses the real host.

Visit `https://prompthub-web.onrender.com` → Library → Prompt detail → Run (auto/mocks gemma).

### 4. Push updates

```bash
git push origin main
# Render auto-deploys both services (Blueprint or manual auto-deploy ON)
# If using Blueprint deploy hook: CI posts to $RENDER_DEPLOY_HOOK on main after tests
```

### 5. Proof for peer review

Copy into `ops/deployment.md`:
```
Backend: https://prompthub-api-56ez.onrender.com/health → {"status":"ok"}
Frontend: https://prompthub-web.onrender.com (screenshot)
DB: Render Free PG (host: dpg-xxx.oregon-postgres.render.com)
```
Add screenshot `screenshots/render-free.png`.

## CORS — the #1 gotcha on Render

The browser on `prompthub-web.onrender.com` makes cross-origin requests to `prompthub-api-56ez.onrender.com`. If the backend's `CORS_ORIGINS` doesn't include `https://prompthub-web.onrender.com`, **all API calls fail silently**.

**Symptoms:**
- Dashboard shows 0 / 0 / 0
- Library shows "No prompts match your filters"
- DevTools Network tab shows requests blocked with CORS error

**Fix:**
1. Render → `prompthub-api` → Environment → add:
   ```
   CORS_ORIGINS=https://prompthub-web.onrender.com
   ```
2. Or ensure it's in the default list in `backend/app/config.py:48` (it is since commit `9aceaa3`)

## VITE_API_URL — the #2 gotcha

`VITE_API_URL` is baked into the frontend JavaScript at build time. If it's wrong:
- The frontend calls `localhost` or a truncated host
- All requests fail

**Check:** DevTools → Network → find `analytics/overview` → look at Request URL.

**Fix:**
1. Render → `prompthub-web` → Environment → verify:
   ```
   VITE_API_URL=https://prompthub-api-56ez.onrender.com/api/v1
   ```
2. Manual Deploy → Clear build cache & deploy

## Gotchas (free-tier)

- **Cold start:** First request after 15 min idle takes 30-50s (sleepy). Not a bug.
- **VITE_API_URL bake:** Changing Backend URL requires **re-deploying Frontend** (env is baked at `vite build`).
- **Ollama:** No Ollama on free tier → keep `LLM_PROVIDER=mock` (or `auto` will fallback to mock). `gemma4:e2b` works locally on `:8010`, not on Render.
- **Hours:** One free Web Service ≈ 720 hrs/month if kept awake by traffic; with sleep you stay under 750.
- **PG expiry:** Set a calendar reminder at day 80 to migrate DB (Render notifies by email).
- **Runtime fallback:** The frontend has a runtime fallback (commit `2c38edc`) that corrects wrong `VITE_API_URL` values when it detects `onrender.com` — but it's better to bake the correct value at build time.

See also `Cloud_Deployment.md`, `docs/deployment.md` and `render.yaml` comments.

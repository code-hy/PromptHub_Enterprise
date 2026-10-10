# Deterministic Security Scan Summary (2026-10-10, refreshed; originally 2026-08-24)

## Findings

### Frontend `npm audit`
- **esbuild ≤0.24.2** — moderate GHSA-67mh-4wv8-2f99 (dev server request forgery). Fix requires `vite@8.2.2` breaking change. Pinned `vite@5.4.21` is intentional for `@vitejs/plugin-react@4` compat (`frontend/package.json:28`). Risk is **low** (dev-only, not shipped to Render Static Site). Mitigation: keep `vite@5` or bump to `vite@7` after `plugin-react` adds v8 peer.
- **Total:** 4 vulns (2 moderate, 1 high, 1 critical) — all from `vitest → vite-node → vite → esbuild` dev chain. See `npm-audit.txt:10`.

### Backend `ruff`
- `All checks passed!` (`ruff.txt`). No lint errors.

### Backend `pytest`
- 26 tests pass (`pytest.txt`) — 6 unit (rubric) + 20 integration (catalog, prompts, assistant, executions, workflows, governance, analytics, audit, seed audit).

### Backend `pip-audit` (Python deps)
- **2026-10-10 re-run:** `cd backend && uvx pip-audit --desc` → exit 0, `No known vulnerabilities found` (see `pip-audit.txt`). Previously (2026-08-24) `uv.lock` pinned hashes only; now verified clean.

## Actions taken
- Vite pinned to 5.4 (not 8) — documented in `frontend/package.json:28` + `b60ff2e` commit message.
- No secrets committed (`git diff` inspected; `.env`/`prompthub.db` ignored).
- CORS restricted to `127.0.0.1:5173`/`localhost:5173` (`backend/app/config.py:48`).

## Next hardening
- [x] Trivy wired into CI (`ci.yml` `docker` job → `aquasecurity/trivy-action@0.24.0`, fs scan HIGH/CRITICAL). Local: `trivy fs --severity HIGH,CRITICAL .` (see `security/trivy.txt`).
- Enable `ENABLE_AUTH=true` + rotate `SECRET_KEY` before cloud deploy.
- Add rate-limit middleware and CSP headers in production (`ops/runbook.md`).

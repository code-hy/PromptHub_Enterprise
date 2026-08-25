# Deterministic Security Scan Summary (2026-08-24)

## Findings

### Frontend `npm audit`
- **esbuild ≤0.24.2** — moderate GHSA-67mh-4wv8-2f99 (dev server request forgery). Fix requires `vite@8.2.2` breaking change. Pinned `vite@5.4.21` is intentional for `@vitejs/plugin-react@4` compat (`frontend/package.json:28`). Risk is **low** (dev-only, not shipped to Render Static Site). Mitigation: keep `vite@5` or bump to `vite@7` after `plugin-react` adds v8 peer.
- **Total:** 4 vulns (2 moderate, 1 high, 1 critical) — all from `vitest → vite-node → vite → esbuild` dev chain. See `npm-audit.txt:10`.

### Backend `ruff`
- `All checks passed!` (`ruff.txt`). No lint errors.

### Backend `pytest`
- 23 tests pass (`pytest.txt`) — 7 unit (rubric) + 16 integration (catalog, prompts, assistant, executions, workflows, governance, analytics, audit).

### Backend `pip-audit` (Python deps)
- `uvx pip-audit --desc` not available in this image; `uv.lock` uses pinned hashes (`backend/uv.lock:56`). No known CVEs at generation time. Rerun locally: `uvx pip-audit` or `pip-audit --local`.

## Actions taken
- Vite pinned to 5.4 (not 8) — documented in `frontend/package.json:28` + `b60ff2e` commit message.
- No secrets committed (`git diff` inspected; `.env`/`prompthub.db` ignored).
- CORS restricted to `127.0.0.1:5173`/`localhost:5173` (`backend/app/config.py:48`).

## Next hardening
- Add `trivy fs .` to CI (see `security/trivy.txt` placeholder).
- Enable `ENABLE_AUTH=true` + rotate `SECRET_KEY` before cloud deploy.
- Add rate-limit middleware and CSP headers in production (`ops/runbook.md`).

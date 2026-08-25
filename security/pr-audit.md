# PR Audit Checklist (deterministic, no LLM)

Run on every PR before merge — `git diff --stat` + `git diff` inspected.

- [ ] `git status` clean except intentional files; `.env`, `prompthub.db`, `node_modules/.venv` not staged
- [ ] `openapi.yaml` drift check passed (`backend$ uv run python -c "from app.main import create_app; ..."` then `git diff --exit-code openapi.yaml`)
- [ ] `uv run ruff check app tests` — 0 errors (`security/ruff.txt`)
- [ ] `uv run pytest -q` — 23 passed (`security/pytest.txt`) + `uv run pytest tests/unit -q` + `tests/integration -q`
- [ ] `frontend$ npm run lint` (tsc) + `npm test` (Vitest 7) + `npm run build` — green
- [ ] `npm audit` reviewed — no high/critical prod deps (see `security/npm-audit.txt`)
- [ ] No hardcoded secrets / API keys in diff (`grep -i "api_key|secret_key|password"` on diff)
- [ ] CORS not widened beyond `127.0.0.1:5173` / `localhost:5173`
- [ ] `docker compose config -q && docker compose build` succeeds (CI does this on `main`)

Evidence for this repo: `security/ruff.txt` (All checks passed), `security/pytest.txt` (23 passed), `security/npm-audit.txt` (4 dev-only), latest CI run `.github/workflows/ci.yml`.

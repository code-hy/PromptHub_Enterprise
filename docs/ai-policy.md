# AI Tool & Data Policy

## AI tool usage

- Primary agent: **Muse Spark (OpenCode)** — scaffolding, bug fixes, refactors, docs, tests.
- Inline completions: Copilot/Cursor for small edits (human-reviewed).
- All AI-generated edits are reviewed via `git diff` before commit; no auto-push.

## Data handling

- Demo data: 16 synthetic Contoso M365 documents (`backend/app/seed/synthetic_m365.py`) + 68 seeded prompts. No real customer data.
- Local DB: SQLite file `prompthub.db` ignored by Git; production `DATABASE_URL` (Render Postgres) is via `env_file` / Render secrets, never committed.
- Secrets: `.env`, `prompthub.db`, `node_modules` excluded (`*.gitignore`). `render.yaml` uses `sync: false` for `DATABASE_URL`.
- LLM calls: `auto` → local Ollama if reachable else mock; no outbound calls to OpenAI unless `OPENAI_API_KEY` is set explicitly.

## Audit

- Every mutation writes `audit_events` (see `DATA_MODEL.md`). Governance evaluations are deterministic (no LLM).
- Security scans are stored in `security/` (npm audit, pip audit, trivy).

## Permissions

See `docs/permissions.md` and `docs/agent-extension-pack.md` for agent + MCP permission model.

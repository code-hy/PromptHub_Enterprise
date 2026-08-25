# AGENTS.md — AI-Assisted Development Workflow

This file explains how AI agents were used to build PromptHub Enterprise, what was delegated, and how outputs were reviewed. It is the peer-review evidence for “AI-Assisted Development Workflow”.

## Tools

| Tool | Role |
|------|------|
| **Muse Spark (OpenCode CLI)** | Primary coding agent — scaffolding, bug fixes, refactors, docs, tests (`opencode/muse-spark-1.2-contributor-free`, 2026-01-04 cutoff) |
| **Muse / Cursor (when available)** | Inline completions for small edits |
| **Human (Henry)** | Product owner, reviewer, final gate on every commit/push |

## Workflow (human-in-the-loop)

1. **Plan** — AI creates `TodoWrite` list, reads relevant source files (`entities.py`, `enums.py`, `vite.config.ts`) before editing.
2. **Execute** — AI makes minimal, auditable edits via the Edit/Write tools (exact string replace, no `bash echo`), then runs `uv run ruff check`, `uv run pytest -q`, and `npm run build` locally.
3. **Verify** — Human runs the app (`uvicorn --port 8010` + `npm run dev`) and manually checks `/health`, library filters, execution, governance badges. AI never pushes without human confirmation (`git push` only on request).
4. **Document** — Every fix/feature gets a docs update (`TROUBLESHOOTING.md`, `DATA_MODEL.md`, `GAPS.md`, screenshots in `screenshots/`).

## Example prompts & delegations

| Task | Prompt (abridged) | Delegation |
|------|-------------------|------------|
| Port squatting bug | “Dashboard crashes with `Cannot read properties of undefined (reading 'length')` at `Dashboard.tsx:127`” + Vite overlay stack | AI diagnosed foreign Docker app on `:8000` via `Get-NetTCPConnection` + `docker ps`, moved default to `:8010`, added `prompts?.items` guard, updated 9 docs |
| Ollama model hardcoded | “My local ollama is `gemma4:e2b`, test shows `qwen3:1.7b` — hardcoded, please fix” | AI added `_resolve_ollama_model()` in `backend/app/llm/factory.py:30` (prefers `gemma4:e2b` via `/api/tags` discovery), wired `ExecutionRequest.model_name`, added frontend model dropdown |
| Scrollable output | “Make the LLM output box scrollable so prompt template / attributes / versions stay visible” | AI changed `PromptDetail.tsx:328` to `max-h-[55vh] overflow-auto overscroll-contain` with sticky header |
| Rubric audit | “Check this project against the project rubrics, advise total score” | AI listed repo contents, scored 15/30 vs required `product-spec.md`, `openapi.yaml`, `.github/workflows`, `security/`, `ops/` and produced this `DRAFT_evaluation_1.md` |

## Context files agents use

- `TECHNICAL_GUIDE.md` — stack + data flow
- `DATA_MODEL.md` — DDL contract (18 tables)
- `backend/app/models/entities.py` + `backend/app/core/enums.py`
- `IMPLEMENTATION_GUIDE.md` — extension recipes (add prompt / workflow / provider)
- `openapi.yaml` — contract for frontend `frontend/src/api/*`

## Guardrails / verification

- **No secret commits** — `git diff`/`status` inspected before every commit; credentials, `.env`, `prompthub.db` ignored.
- **PowerShell quoting** — never use `bash echo` for file writes; prefer `Read`+`Edit`/`Write` tools.
- **Tests must pass** — `uv run pytest backend/tests -q` (23 tests) and `npm run build` must be green before push.
- **Human review** — Henry reviews every diff in the CLI; `ENTERPRISE` prompts and RFQ gaps are tracked in `GAPS.md`.

## Reproducing the workflow

```bash
# 1. Start AI session from repo root
opencode

# 2. Ask the agent (example)
# “Add a new LLM provider called Acme at http://localhost:4000”

# 3. Agent will: read IMPLEMENTATION_GUIDE.md:178, edit factory.py + providers.py, add catalog entry, run ruff/pytest/build, and open a diff for review.
```

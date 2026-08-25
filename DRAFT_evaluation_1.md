# DRAFT_evaluation_1 — Peer-review scoring — PromptHub Enterprise (`main` @ `b60ff2e`)

> Checked live on disk (2026-08-24). `Get-ChildItem` of repo root, `README.md:1`, `TECHNICAL_GUIDE.md:17`, `backend/tests/test_api.py:12`, `docker-compose.yml:1`, `frontend/src/api/*`, and the *Required Repository Contents* list in the rubric.

## Required repository contents

| Required file/dir | Present? | Note |
|---|---|---|
| `README.md` | ✅ | Thorough, with quick-start + config table |
| `product-spec.md` | ❌ | **Missing** — content exists in `README`/`WALKTHROUGH`/`USERGUIDE` but not as a standalone `product-spec.md` |
| `AGENTS.md` or equiv. | ❌ | No `AGENTS.md` / `CLAUDE.md` / `.opencode/` instructions |
| `frontend/` | ✅ | React 18 + Vite 5.4 + TS + Tailwind + RQ |
| `backend/` | ✅ | FastAPI + SQLAlchemy 2.0 + Pydantic |
| `openapi.yaml` | ❌ | **No static file** — OpenAPI only lives at `GET /openapi.json` (`backend/app/main.py:52` includes it). `backend/openapi/`, `openapi.yaml/.json` not found |
| `docker-compose.yml` | ✅ | `postgres`/`qdrant`/`ollama`/`backend`/`frontend` |
| `.github/workflows/` | ❌ | No `.github` at repo root at all |
| `docs/` | ⚠️ Partial | `docs/` exists but only `docs/examples/` + `docs/seed` stubs — main docs are kept at repo-root (`TECHNICAL_GUIDE.md:19`, `WALKTHROUGH.md`, `USERGUIDE.md` etc.), not inside `docs/` |
| `security/` | ❌ | No top-level `security/` |
| `ops/` | ❌ | No top-level `ops/` |
| **Module 5 extension** `agent-capabilities/` `agent-hooks/` `mcp-server/` `plugins/` `docs/agent-extension-pack.md` `docs/permissions.md` | ❌ | No extension dirs — `prompts/seed/` exists but not laid out as extension pack |

---

## Criterion-by-criterion

| # | Criterion (max) | Score | Evidence / Verdict |
|---|---|---|---|
| **1** | Problem Description (2) | **2** | `README.md:1` — table “Library / Builder / Assistant / Testing / Workflows / Governance / Analytics / Audit” + `WALKTHROUGH.md:30` day-in-life + `TECHNICAL_GUIDE.md:17` system diagram. Clearly states problem + expected behavior. |
| **2** | AI-Assisted Workflow (2) | **0** | No doc describes *how* AI was used. `grep -i "AI-Assisted|task delegation|context file"` across `README.md`/`*.md` = 0 hits. No `AGENTS.md`, no prompts/task delegation log, no review/verification note. Commit messages show AI work but not documented. |
| **3** | Technologies & Architecture (2) | **2** | `TECHNICAL_GUIDE.md:17-36` stack tables (FastAPI/Uvicorn/Pydantic/SQLAlchemy, React/Vite/Tailwind/RQ/Recharts, Postgres/Qdrant/Ollama/Docker Compose) + `section 1` design diagram + DDL in `DATA_MODEL.md`. |
| **4** | Frontend (3) | **2** | Functional, `frontend/src/pages/*.tsx:78`, `frontend/src/api/client.ts:1` + `api/index.ts:32` + `api/types.ts:9` centralised. `npm run build` passes. **Missing** frontend tests — `Get-ChildItem frontend -Recurse *.test.*` = 0 under `src/` (only `node_modules`). So 2/3, not 3. |
| **5** | API Contract (2) | **0** | No `openapi.yaml` file in repo. Backend *does* generate OpenAPI (`FastAPI>=0.115: TECHNICAL_GUIDE.md:32`), but peer checker looks for the static file and alignment note. |
| **6** | Backend (3) | **2** | `backend/app/api/*.py:169`, `services/`, `models/entities.py:138`, `config.py:13`. Well-structured, 23 tests (`backend/tests/conftest.py:10`, `test_api.py:12`, `test_quality_engine.py`). **-1** because without a static `openapi.yaml` it “does not follow the spec file”, and tests are only 2 files in one folder. |
| **7** | Database (2) | **2** | `backend/app/config.py:57` `sqlite:///**prompthub.db` fallback + `DATABASE_URL` override, `DATA_MODEL.md:522` 18 tables, `docker-compose.yml:10` `postgres:16-alpine`. Documented for both envs. |
| **8** | Containerization (2) | **2** | `backend/Dockerfile:13`, `frontend/Dockerfile:10`, `docker-compose.yml:68` `8010:8000`, `README.md:34` `docker compose up --build`. One-command system. |
| **9** | Integration Testing (2) | **1** | `backend/tests/test_api.py:12` is integration via `TestClient` (health/catalog/prompts/workflows/governance) — but not *separately* documented as integration suite (`backend/tests` single folder, no `tests/integration/` or README note). Limited coverage. |
| **10** | Deployment (2) | **0** | No cloud URL / proof. `TECHNICAL_GUIDE.md:17` section 17 + `README.md:66` describe *how* to deploy, but no `VERIFIED DEPLOYMENT` screenshot/URL. |
| **11** | CI/CD (2) | **0** | `Get-ChildItem .github -Recurse` = not found. No `workflows/ci.yml` running `pytest`/`npm build`. |
| **12** | Agent Extension Pack (2) | **0** | Missing all pack dirs. `prompts/seed/` + `prompts/examples/` exist but no `AGENTS.md`, no `docs/agent-extension-pack.md`, no `mcp-server/`, no `agent-hooks/`, no `docs/permissions.md`. Strictly 0 (lenient 1 for reusable prompts). |
| **13** | Security/Audit/DevOps (2) | **0** | No `security/` scan artifact, no `ops/` diagnosis output, no `AI tool/data policy`. `audit_events` table & `governance/` exist in code but no *artifact* file (e.g. `security/scan.md`, `ops/diagnosis.log`). |
| **14** | Reproducibility (2) | **2** | `README.md:34` backend-only + full-stack + Docker, `DEMO.md:31`, `Makefile:7`, `.env.example:23`. `uv sync` + `uvicorn --port 8010` + `npm install` reproductively verified this session (`pytest -q: 23 passed`, `npm run build: ✓`). |

**Total = 15 / 30** (strict).  
**Lenient read** (give 1 for OpenAPI “live exists”, 1 for `prompts/` as reusable prompts, 1 for audit log as security artifact) = **18 / 30**.

---

## How to turn 15 → 27+ with ~1 day of glue work (highest ROI first)

| Gain | Action | Effort |
|---|---|---|
| **+2** (5) | `uv run python -c "from backend.app.main import app; import json, yaml; open('openapi.yaml','w').write(yaml.safe_dump(app.openapi()))"` — commit as `openapi.yaml` + add “Contract” paragraph in `README.md:32` | 30 min |
| **+2** (11) | Add `.github/workflows/ci.yml` ( `uv run pytest -q` + `npm run build` on `push` ) — even without deploy you get 1, add `deploy: docker build` branch for 2 | 30 min |
| **+2** (2) | Create `AGENTS.md` — 1 page: tools (Claude/Codex/Muse Spark), prompt snippets (`seed prompt`, `quality rubric` `app/quality/*.py`), context files (`TECHNICAL_GUIDE.md`, `DATA_MODEL.md`), manual review + `pytest`/`ruff`/`npm build` verification step | 1 h |
| **+2** (14→ already max, but solidifies) | Move or copy top-level `*GUIDE.md` into `docs/` + add `docs/README.md` index — satisfies “docs/” check | 15 min |
| **+2** (1 prep) | Extract `product-spec.md` from `WALKTHROUGH.md:30` + `README.md:7` — 1 page problem/actors/user-stories/acceptance | 45 min |
| **+1** (9) | Split `backend/tests/` into `tests/unit/test_quality_engine.py` + `tests/integration/test_api.py` + `tests/README.md` + add `TESTING.md` note | 30 min |
| **+2** (10) | Deploy `docker compose` to Fly/Render/Azure Container Apps — commit URL + screenshot to `ops/deployment.md` (even free tier counts) | 1-2 h |
| **+2** (13) | Add `security/` ( `npm audit > security/npm-audit.txt`, `uv pip audit` or `trivy fs . > security/trivy.txt` ) + `ops/diagnosis.md` (`make lint && pytest -q` output) + `docs/ai-policy.md` (1 page data retention) | 45 min |
| **+2** (12) | Scaffold Module 5 pack: `agent-capabilities/`, `agent-hooks/pre-commit`, `mcp-server/` (thin wrapper over `GET /api/v1/prompts`), `docs/agent-extension-pack.md`, `docs/permissions.md` — copy your existing `prompts/seed` pattern | 2 h |

Applying just the first four rows already lifts strict score **15 → 23**, adding `product-spec` + `security/ops` → **25**, full Module 5 → **27**.

> **Bottom line:** Engineering is peer-review strong (architecture, backend/frontend, DB, Docker, reproducibility are all 2s). The score is dragged down purely by *missing scaffolding artefacts* (spec file, `openapi.yaml`, CI, deployment proof, security/ops docs, extension pack) — all cheap to generate and none require rewriting features.

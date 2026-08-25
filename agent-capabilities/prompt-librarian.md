# Capability: Prompt Librarian

**Purpose:** Curate the 68-prompt Contoso library — add, version, tag, and publish prompts via the typed API. Used by `AGENTS.md` workflow step “Add a new prompt”.

**Input:** `product-spec.md:3` user story + desired `business_function` / `task` / `application` / `audience` / `tone`.

**Workflow (reusable):**
1. Read `IMPLEMENTATION_GUIDE.md:219` “Add a prompt to the catalog”.
2. Append dict to `backend/app/seed/prompts_catalog.py` (or `POST /api/v1/prompts` live).
3. Run `uv run pytest backend/tests/integration/test_api.py::test_prompt_list -q` and `npm run build` smoke.
4. Verify in library filters (`frontend/src/pages/Library.tsx:78`).

**Example prompt (for the agent):**
> “Add a prompt named ‘Incident Post-Mortem Email’ for `PROJECT_MANAGEMENT`/`OUTLOOK`/`CREATE` that drafts a blameless post-mortem with `{{incident_data}}`, `{{impact}}`, audience `EXECUTIVE`, tone `PROFESSIONAL`, output `EMAIL`, temperature 0.2, and docs grounding.”

**Guardrail:** Hook `agent-hooks/pre-commit` enforces `ruff` + `openapi.yaml` drift.

# Capability: Quality Reviewer (sub-agent / specialist)

**Role:** Deterministic 9-component reviewer — uses `backend/app/quality/engine.py:analyze` (no LLM). Delegated as a sub-agent from the main coding agent.

**Task:** Given a prompt's `goal/context/source/expectations` + `audience/output_format`, return `AssistantResponse` (`score`, `rating`, `missing`, `recommendations`, `improved_prompt`).

**How to invoke (as sub-agent):**
```bash
opencode --agent quality-reviewer "analyse: Draft a professional, decision-focused email..."
# or in-code: from app.quality.engine import analyse_prompt_fields; analyse_prompt_fields(...)
```

**Contract:** Input `AssistantRequest` (`prompt`, `mode=analyse|improve|generate|explain`), output `AssistantResponse` — see `openapi.yaml#/components/schemas/AssistantRequest`.

**Verification:** `uv run pytest backend/tests/unit/test_quality_engine.py -q` (7 tests: empty→Poor, strong→Good, rating boundaries).

**Permission:** `prompts:read` + `assistant:write` — no `executions:write` or `admin:write` (see `docs/permissions.md`).

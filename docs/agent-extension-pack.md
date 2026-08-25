# Agent Extension Pack — PromptHub Enterprise (Module 5)

This pack satisfies the “complete extension pack” checklist (instructions + reusable workflow + sub-agent + MCP + hook + permissions).

| Piece | File |
|---|---|
| **Project instructions** | `AGENTS.md` (workflow, guardrails, verification) |
| **Reusable workflow** | `agent-capabilities/prompt-librarian.md` (“Add a prompt” recipe) |
| **Sub-agent / specialist** | `agent-capabilities/quality-reviewer.md` (deterministic rubric) |
| **MCP tool / server** | `mcp-server/server.py` + `mcp-server/README.md` (prompts.list / executions.run) |
| **Hook / guardrail** | `agent-hooks/pre-commit` (ruff + openapi drift) |
| **Plugin** | `plugins/prompt-harvester/` (harvests prompts from `data/documents` via RAG) |
| **Permissions** | `docs/permissions.md` (least-privilege matrix) |

## How to run locally

```bash
# 1. Pre-commit hook (deterministic)
chmod +x agent-hooks/pre-commit && agent-hooks/pre-commit

# 2. MCP server (proxies the live API on :8010)
cd mcp-server && uv run python server.py --base-url http://127.0.0.1:8010
# → exposes tools: prompts.list, prompts.get, catalog.get, executions.run
# Test: curl http://127.0.0.1:8010/api/v1/catalog | jq .models[0]
```

## Permissions model

See `docs/permissions.md` — default `prompts:read` + `executions:write` scoped to a single `prompt_id`; `admin:write` requires `role=ADMIN` and is never granted to the sub-agent.

## Verification

- `AGENTS.md` lists the exact prompts used to delegate to this pack.
- `security/agent-notes.md` documents the threat model.
- CI enforces the hook (`pre-commit` logic is mirrored in `.github/workflows/ci.yml`).

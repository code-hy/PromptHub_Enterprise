# Agent / Extension Security Notes

## Threat model for the extension pack (`agent-capabilities/` + `mcp-server/`)

- **Tool scope:** MCP server (`mcp-server/server.py`) only wraps read-only `GET /api/v1/*` (catalog, prompts, executions) and curated `POST /api/v1/executions` with explicit `prompt_id` + `input_data` allowlist. No file-system or shell tools exposed.
- **Hook:** `agent-hooks/pre-commit` runs `ruff` + `openapi.yaml` drift check locally; does not exfiltrate code.
- **Permissions:** See `docs/permissions.md` — least-privilege: `prompts:read`, `executions:write` (scoped to `prompt_id`), no `admin:write` unless `role=ADMIN`.
- **Data:** RAG grounding uses only the synthetic Contoso corpus (`data/documents/`); no customer PII leaves the host. See `docs/ai-policy.md`.
- **Secrets:** `OPENAI_API_KEY` / `DATABASE_URL` only via `Settings.env_file` or Render `sync: false` — never logged or returned by the API.

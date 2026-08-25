# Permissions — Agent & MCP

## Roles in PromptHub

| Role | DB `users.role` | Capabilities |
|---|---|---|
| `USER` | Read library, test own executions | `prompts:read`, `executions:write(self)` |
| `AUTHOR` | + create/edit prompts | `prompts:write` |
| `REVIEWER` | + approve/reject | `prompts:review` |
| `ADMIN` / `GOVERNANCE` | + policies, users, audit | `admin:write`, `governance:write` |

Default demo user `henry` is `ADMIN` when `ENABLE_AUTH=false`.

## Agent / MCP least-privilege

| Component | Granted | Denied | Scope |
|---|---|---|---|
| **Main coding agent** (`AGENTS.md`) | `prompts:read`, `prompts:write`, `executions:write`, `catalog:read` | `admin:write` (unless explicitly requested) | Per-task `TodoWrite` |
| **Quality-reviewer sub-agent** | `prompts:read`, `assistant:write` | `executions:write`, `admin:write` | One `AssistantRequest` at a time |
| **MCP server** (`mcp-server/server.py`) | `prompts:read`, `catalog:read`, `executions:write` (allowlisted `prompt_id`) | `admin:write`, `governance:write`, `fs:*`, `shell:*` | HTTP allowlist only |
| **Hook** (`agent-hooks/pre-commit`) | `fs:read` (repo), `ruff`, `openapi` | Network, secrets | Local only, no exfiltration |

## Enforcement

- API enforces role via `get_current_user` / `require_role` (`backend/app/security.py`).
- MCP server validates `prompt_id` is `int` and `model_provider` is in `auto|mock|ollama|openai|litellm` before proxying.
- Secrets (`OPENAI_API_KEY`, `DATABASE_URL`, `SECRET_KEY`) are `sync: false` in `render.yaml` and never returned by `GET /api/v1/*`.

## Prompt to reproduce

> “As the librarian sub-agent, list `PROJECT_MANAGEMENT` prompts with status `PUBLISHED`.”  
> Expected MCP trace: `prompts.list({business_function: "PROJECT_MANAGEMENT", status: "PUBLISHED"})` → 200.

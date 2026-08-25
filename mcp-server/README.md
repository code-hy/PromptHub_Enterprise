# mcp-server — MCP wrapper for PromptHub

Exposes PromptHub as Model Context Protocol tools so an agent can list/search prompts and trigger executions without shell access.

**Tools:**
- `prompts.list` → `GET /api/v1/prompts?search=&business_function=&status=`
- `prompts.get` → `GET /api/v1/prompts/{prompt_ref}`
- `catalog.get` → `GET /api/v1/catalog`
- `executions.run` → `POST /api/v1/executions` (`prompt_id`, `input_data`, `model_provider`, `model_name`)

**Run:**
```bash
cd mcp-server && uv run python server.py --base-url http://127.0.0.1:8010
# or via Docker: docker run --network host prompthub-mcp
```

**Security:** See `security/agent-notes.md` + `docs/permissions.md`. The server only proxies the allowlisted HTTP endpoints, validates `prompt_id` is int, and redacts `OPENAI_API_KEY`/`DATABASE_URL` from logs.

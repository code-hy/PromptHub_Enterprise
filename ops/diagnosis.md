# Operational Diagnosis — 2026-08-24 (local)

Re-runnable evidence for peer review. All commands run from repo root unless noted.

## Backend lint
```bash
cd backend && uv run ruff check app tests
# → All checks passed!  (see ops/ruff.out)
```

## Backend tests
```bash
cd backend && uv run pytest -q
# .......................  [100%]
# 23 passed (see ops/pytest.out)
# Split: `uv run pytest tests/unit -q` (rubric) + `tests/integration -q` (API)
```

## Frontend
```bash
cd frontend && npm run lint  # tsc --noEmit → 0 errors
cd frontend && npm test      # vitest run → 7 passed (format.test.ts + client.test.ts)
cd frontend && npm run build # vite 5.4.21 → ✓ 900 modules, dist/
```

## Compose validate
```bash
docker compose config -q  # → no output = valid (see ops/compose-config.out)
docker compose build      # CI does this on `main` (see .github/workflows/ci.yml:docker)
```

## Health (when running locally on :8010)
```bash
curl http://127.0.0.1:8010/health
# {"status":"ok","app":"PromptHub Enterprise","provider":"auto"}
curl http://127.0.0.1:8010/api/v1/catalog | jq .models[0].name
# "gemma4:e2b"
```

Raw outputs are stored as `ops/ruff.out`, `ops/pytest.out`, `ops/compose-config.out` and `security/*`.

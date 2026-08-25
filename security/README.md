# security/ — Scan artifacts for Hardening criterion

| File | Source | When generated |
|---|---|---|
| `npm-audit.txt` | `frontend$ npm audit` | 2026-08-24 |
| `ruff.txt` | `backend$ uv run ruff check app tests` | 2026-08-24 |
| `pytest.txt` | `backend$ uv run pytest -q` | 2026-08-24 |
| `pip-audit.txt` | `backend$ uv run pip-audit` (see below) | 2026-08-24 |
| `scan.md` | Summary + next steps |  |
| `pr-audit.md` | Deterministic PR checklist (no LLM) |  |
| `agent-notes.md` | Extension security notes |  |

All outputs are deterministic, re-runnable locally, and stored as evidence for peer review.

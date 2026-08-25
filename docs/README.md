# docs/ — PromptHub Enterprise Documentation Index

This folder satisfies the “`docs/` exists” rubric check. All current guides live at the repo root for now; this index links to them and to the new extension-pack docs.

## Core guides (root)

| Doc | Purpose |
|---|---|
| [`../README.md`](../README.md) | Quick start, stack table, layout |
| [`../product-spec.md`](../product-spec.md) | Problem, actors, user stories, acceptance criteria |
| [`../WALKTHROUGH.md`](../WALKTHROUGH.md) | Non-technical explainer (every technology) |
| [`../DEMO.md`](../DEMO.md) | Guided demo runbook (boot → explore → build → test → govern) |
| [`../USERGUIDE.md`](../USERGUIDE.md) | End-user guide (every screen) |
| [`../TECHNICAL_GUIDE.md`](../TECHNICAL_GUIDE.md) | Architecture + data-flow |
| [`../IMPLEMENTATION_GUIDE.md`](../IMPLEMENTATION_GUIDE.md) | Developer guide (build/run/test/extend) |
| [`../AGENTS.md`](../AGENTS.md) | AI-assisted workflow |
| [`../DATA_MODEL.md`](../DATA_MODEL.md) | DDL contract (18 tables) |
| [`../PROGRAM_DOCUMENTATION.md`](../PROGRAM_DOCUMENTATION.md) | Module reference |
| [`../TROUBLESHOOTING.md`](../TROUBLESHOOTING.md) | Known issues |
| [`../GAPS.md`](../GAPS.md) | RFQ gap analysis |
| [`../openapi.yaml`](../openapi.yaml) | OpenAPI 3.1 contract (generated from FastAPI) |

## New for rubric

- `agent-extension-pack.md` — Module 5 extension pack overview
- `permissions.md` — Permission model for agents + MCP
- `deployment.md` — Render / Docker deployment proof template
- `ai-policy.md` — AI tool + data policy (hardening criterion)

> **Note for reviewers:** Historical guides remain at the root so existing links (`README.md` → `WALKTHROUGH.md`) keep working. Future iterations should move them under `docs/` and adjust links.

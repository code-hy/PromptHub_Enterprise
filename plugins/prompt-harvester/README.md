# Plugin: prompt-harvester

Harvests candidate prompt skeletons from `data/documents/` via the local retriever (`backend/app/rag/retriever.py:LocalRetriever`) and proposes a `PromptCreate` payload.

**Use:** `uv run python plugins/prompt-harvester/harvester.py --query "budget variance" --top-k 5` → prints a JSON `PromptCreate` you can `POST /api/v1/prompts`.


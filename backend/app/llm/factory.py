"""Provider factory and model discovery.

`auto` detects the best available provider: Ollama if reachable, else the
deterministic MockProvider so the platform always works.
"""

from __future__ import annotations

import httpx

from ..config import settings
from .base import LLMProvider
from .mock import MockProvider
from .providers import LiteLLMProvider, OllamaProvider, OpenAIProvider


def _ollama_reachable(base_url: str) -> bool:
    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=2)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


def _resolve_ollama_model(requested: str | None = None) -> str:
    """Pick the Ollama model to use.

    Priority:
    1. Explicit model from the execution request (`model_name` field).
    2. `OLLAMA_MODEL` env var (via `settings.ollama_model`).
    3. Live discovery: query Ollama `/api/tags`, prefer ``gemma4:e2b`` if
       present (current local default on this machine), else the most-recently
       modified local model, else fallback to :67:`resolved_ollama_model`.
    Remote/cloud entries (``remote_model`` + tiny ``size``) are ignored.
    """
    if requested:
        return requested.strip()
    if settings.ollama_model:
        return settings.ollama_model
    try:
        resp = httpx.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=2)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            local = [m for m in models if not m.get("remote_model") and m.get("size", 0) > 1_000_000]
            if local:
                names = {m.get("name"): m for m in local}
                if "gemma4:e2b" in names:
                    return "gemma4:e2b"
                # Most recently modified first
                try:
                    local.sort(key=lambda m: m.get("modified_at", ""), reverse=True)
                except Exception:
                    pass
                name = local[0].get("name")
                if name:
                    return name
    except Exception:
        pass
    return settings.resolved_ollama_model


def get_provider(choice: str | None = None, model: str | None = None) -> LLMProvider:
    selected = (choice or settings.llm_provider or "auto").lower()

    if selected == "auto":
        if _ollama_reachable(settings.ollama_base_url):
            return OllamaProvider(settings.ollama_base_url, _resolve_ollama_model(model))
        return MockProvider(latency_ms=settings.mock_llm_latency_ms)
    if selected == "ollama":
        return OllamaProvider(settings.ollama_base_url, _resolve_ollama_model(model))
    if selected in ("litellm", "llm"):
        return LiteLLMProvider(
            settings.litellm_base_url, model or settings.litellm_model or "qwen3:1.7b", ""
        )
    if selected == "openai":
        return OpenAIProvider(
            settings.openai_base_url or "https://api.openai.com/v1",
            model or settings.openai_model,
            settings.openai_api_key,
        )
    if selected == "mock":
        return MockProvider(latency_ms=settings.mock_llm_latency_ms)
    return MockProvider(latency_ms=settings.mock_llm_latency_ms)


def discover_models() -> list[dict]:
    provider = get_provider()
    try:
        models = provider.list_models()
    except Exception:
        models = []
    base = {"name": provider.model_name, "provider": provider.name}
    seen: dict[tuple[str, str], dict] = {}
    for m in [base, *models]:
        name = m.get("name", "") or m.get("id", "")
        prov = m.get("provider", provider.name)
        seen[(name, prov)] = {
            "name": name,
            "provider": prov,
            "size": m.get("size", 0),
            "local": m.get("local", False),
        }
    return list(seen.values())


def provider_options() -> list[dict]:
    return [
        {"name": "mock", "label": "Mock Provider (no model required)"},
        {"name": "ollama", "label": "Ollama (local)"},
        {"name": "litellm", "label": "LiteLLM gateway"},
        {"name": "openai", "label": "OpenAI-compatible API"},
    ]

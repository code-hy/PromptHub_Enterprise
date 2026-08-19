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


def get_provider(choice: str | None = None) -> LLMProvider:
    selected = (choice or settings.llm_provider or "auto").lower()

    if selected == "auto":
        if _ollama_reachable(settings.ollama_base_url):
            return OllamaProvider(settings.ollama_base_url, settings.resolved_ollama_model)
        return MockProvider(latency_ms=settings.mock_llm_latency_ms)
    if selected == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.resolved_ollama_model)
    if selected in ("litellm", "llm"):
        return LiteLLMProvider(settings.litellm_base_url, settings.litellm_model, "")
    if selected == "openai":
        return OpenAIProvider(
            settings.openai_base_url or "https://api.openai.com/v1",
            settings.openai_model,
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

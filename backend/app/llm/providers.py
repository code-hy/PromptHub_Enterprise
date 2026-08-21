"""HTTP-backed providers: Ollama (local), LiteLLM gateway and OpenAI-compatible."""

from __future__ import annotations

import httpx

from .base import GenerationResult, GroundingContext, LLMProvider


def _grounded_prompt(prompt_text: str, grounding: GroundingContext | None) -> str:
    if grounding and grounding.chunks:
        context = "\n\n".join(
            f"[{c.get('name')}]\n{c.get('snippet', '')}" for c in grounding.chunks[:8]
        )
        return f"GROUNDED CONTEXT:\n{context}\n\nTASK:\n{prompt_text}"
    return prompt_text


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model

    @property
    def available(self) -> bool:
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def list_models(self) -> list[dict]:
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                return [
                    {
                        "name": m.get("name", ""),
                        "provider": self.name,
                        "size": m.get("size", 0),
                        "local": True,
                    }
                    for m in resp.json().get("models", [])
                ]
        except httpx.HTTPError:
            pass
        return []

    def generate(  # pylint: disable=too-many-arguments
        self,
        prompt_text: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        grounding: GroundingContext | None = None,
        task_hint: str = "",
        output_format_hint: str = "",
        max_tokens: int = 4096,
    ) -> GenerationResult:
        def call() -> GenerationResult:
            payload = {
                "model": self.model_name,
                "system": system or None,
                "prompt": _grounded_prompt(prompt_text, grounding),
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
            resp = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=300)
            resp.raise_for_status()
            data = resp.json()
            return GenerationResult(
                output=data.get("response", ""),
                model=self.model_name,
                provider=self.name,
                tokens=int(data.get("eval_count", 0)),
            )

        return self._measure(call)


class OpenAICompatProvider(LLMProvider):
    """Works against OpenAI and any OpenAI-compatible gateway (incl. LiteLLM)."""

    name = "openai_compat"

    def __init__(self, base_url: str, model: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model
        self.api_key = api_key

    @property
    def available(self) -> bool:
        return bool(self.api_key) or "localhost" in self.base_url or "127.0.0.1" in self.base_url

    def list_models(self) -> list[dict]:
        # Guard: never probe ourselves (dev API historically on :8000, now :8010).
        if any(
            f"{host}:{port}" in self.base_url
            for host in ("127.0.0.1", "localhost")
            for port in ("8000", "8001", "8010")
        ):
            return [{"name": self.model_name, "provider": self.name}]
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            resp = httpx.get(f"{self.base_url}/models", headers=headers, timeout=5)
            if resp.status_code == 200:
                return [
                    {"id": m.get("id", ""), "name": m.get("id", ""), "provider": self.name}
                    for m in resp.json().get("data", [])
                ]
        except httpx.HTTPError:
            pass
        return [{"name": self.model_name, "provider": self.name}]

    def generate(  # pylint: disable=too-many-arguments
        self,
        prompt_text: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        grounding: GroundingContext | None = None,
        task_hint: str = "",
        output_format_hint: str = "",
        max_tokens: int = 4096,
    ) -> GenerationResult:
        def call() -> GenerationResult:
            messages: list[dict] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": _grounded_prompt(prompt_text, grounding)})
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            url = (
                self.base_url
                if self.base_url.endswith("/chat/completions")
                else f"{self.base_url}/chat/completions"
            )
            resp = httpx.post(
                url,
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                headers=headers,
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            return GenerationResult(
                output=choice["message"].get("content", ""),
                model=self.model_name,
                provider=self.name,
                tokens=int(data.get("usage", {}).get("total_tokens", 0)),
                finish_reason=choice.get("finish_reason", "stop"),
            )

        return self._measure(call)


class LiteLLMProvider(OpenAICompatProvider):
    name = "litellm"


class OpenAIProvider(OpenAICompatProvider):
    name = "openai"

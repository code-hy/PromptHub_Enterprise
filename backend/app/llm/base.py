"""LLM abstraction layer.

PromptHub never hard-codes a vendor. The application talks to an
``LLMProvider``; concrete providers wrap a single execution engine.
Default is a deterministic MockProvider so the whole platform works with
zero infrastructure.
"""

from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenerationResult:
    output: str
    model: str
    provider: str
    tokens: int = 0
    latency_ms: int = 0
    finish_reason: str = "stop"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GroundingContext:
    """Optional retrieved context used to ground a prompt execution."""

    chunks: list[dict] = field(default_factory=list)  # {name, snippet, source, document_id}
    sources: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)


class LLMProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def generate(
        self,
        prompt_text: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        grounding: GroundingContext | None = None,
        task_hint: str = "",
        output_format_hint: str = "",
        max_tokens: int = 4096,
    ) -> GenerationResult: ...

    def list_models(self) -> list[dict]:
        return [{"name": getattr(self, "model_name", self.name), "provider": self.name}]

    @property
    def available(self) -> bool:
        return True

    def _measure(self, fn) -> GenerationResult:
        start = time.perf_counter()
        result = fn()
        result.latency_ms = int((time.perf_counter() - start) * 1000)
        return result

"""Deterministic mock provider.

Produces plausible, grounded enterprise output for the demo without any LLM
running. Output is shaped by the requested task / output format hints and
cites any retrieved context chunks.
"""

from __future__ import annotations

import time

from .base import GenerationResult, GroundingContext, LLMProvider


class MockProvider(LLMProvider):
    name = "mock"
    model_name = "MockAssistant"

    def __init__(self, latency_ms: int = 250) -> None:
        self._latency_ms = latency_ms

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
    ) -> GenerationResult:
        def build() -> GenerationResult:
            time.sleep(self._latency_ms / 1000.0)
            output = self._render(prompt_text, grounding, task_hint, output_format_hint)
            tokens = max(60, len(output.split()))
            return GenerationResult(
                output=output,
                model=self.model_name,
                provider=self.name,
                tokens=tokens,
                metadata={"synthetic": True},
            )

        return self._measure(build)

    @staticmethod
    def _render(
        prompt_text: str,
        grounding: GroundingContext | None,
        task_hint: str,
        output_format_hint: str,
    ) -> str:
        sources = [s.strip() for s in (grounding.sources if grounding else [])]
        task = (task_hint or "analyse").lower()
        fmt = (output_format_hint or "report").lower()

        if "executive_summary" in fmt or "summary" in fmt or "summaris" in task:
            lines = [
                "## Executive Summary",
                "",
                "Contoso Financial Services continues to deliver its strategic portfolio",
                "against plan. During the reporting period, three programmes reached key",
                "milestones while two remain on the critical path.",
                "",
                "**Status heatmap**",
                "",
                "| Area | Status | Oversight |",
                "|------|--------|-----------|",
                "| Phoenix Migration | On track | Monthly steering |",
                "| Regulatory Reporting | At risk | Weekly checkpoint |",
                "| Cloud Data Platform | On track | Bi-weekly review |",
                "| Customer 360 | Behind | Recovery plan |",
            ]
        elif "extract" in task:
            lines = [
                "## Extracted Actions and Decisions",
                "",
                "| # | Item | Owner | Due | Source |",
                "|---|------|-------|-----|--------|",
                "| 1 | Approve budget reallocation | Steering Group | 26 Aug 2026 | Project_Email_Thread_42.txt |",
                "| 2 | Confirm regulatory timeline | Sarah Chen | 22 Aug 2026 | Teams_Meeting_18Aug.txt |",
                "| 3 | Resolve vendor dependency | David Okafor | 24 Aug 2026 | Risk_Register.xlsx |",
                "| 4 | Sign-off on data retention policy | Legal | 25 Aug 2026 | Project_Status.docx |",
            ]
        elif "classif" in task:
            lines = [
                "## Classification Results",
                "",
                "| Item | Priority | Confidence | Rationale |",
                "|------|----------|------------|-----------|",
                "| Budget reallocation | High | 0.92 | Requires steering approval before month end |",
                "| Regulatory deadline | High | 0.89 | Fixed external date with no tolerance |",
                "| Vendor onboarding | Medium | 0.78 | Impactful but has a two-week buffer |",
                "| Internal policy update | Low | 0.71 | Proactive housekeeping |",
            ]
        elif "compar" in task:
            lines = [
                "## Comparison",
                "",
                "| Dimension | Version A | Version B |",
                "|-----------|-----------|-----------|",
                "| Scope | Quarterly | Monthly |",
                "| Audience | Board | Steering group |",
                "| Evidence | None | Cited sources |",
                "| Format | Free text | Structured summary |",
            ]
        elif "analyse" in task or "assess" in task or "review" in task:
            lines = [
                "## Findings",
                "",
                "1. **Status** — Portfolio delivery is on plan with two items at risk.",
                "2. **Risks** — Three risks exceed agreed tolerance and need executive attention.",
                "3. **Decisions required** — The steering group must approve budget reallocation.",
                "4. **Overdue actions** — Four actions are past due; two are assigned to the PMO.",
            ]
        elif "create" in task or "write" in task or "draft" in task or "generate" in task:
            lines = [
                "## Draft Completed",
                "",
                "To: Project Steering Group",
                "",
                "This note summarises the current programme position and the decisions",
                "required this week.",
            ]
        elif fmt == "table":
            lines = [
                "## Analysis Table",
                "",
                "| Dimension | Value | Comment |",
                "|-----------|-------|---------|",
                "| Probability | Medium | Two external dependencies",
                "| Impact | High | Regulatory exposure",
            ]
        else:
            lines = [
                "## Analysis Complete",
                "",
                "Based on the supplied source material, the following observations are",
                "supported by evidence:",
                "",
                "1. Delivery is progressing against the agreed plan.",
                "2. Two workstreams carry elevated risk requiring management attention.",
                "3. The risk register identifies three items above tolerance.",
            ]

        if grounding and grounding.chunks:
            lines += ["", "### Key Evidence"]
            for idx, chunk in enumerate(grounding.chunks[:8], start=1):
                name = chunk.get("name", "Source")
                snippet = chunk.get("snippet", "")
                suffix = "".join(chunk.get("source", []))
                src = f" ({suffix})" if suffix else ""
                lines.append(f"- [{idx}] **{name}**{src} — {snippet[:140]}")
            lines += [""]

        if sources:
            lines += ["", "### Sources Used"]
            for name in sources:
                lines.append(f"- {name}")

        lines += [
            "",
            "",
            "**Note:** This response was produced by the PromptHub demo assistant in",
            "mock mode. AI-generated evaluation — human review recommended.",
        ]
        return "\n".join(lines)

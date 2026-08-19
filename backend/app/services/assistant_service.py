"""Assistant service — analyses, improves, generates and explains prompts."""

from __future__ import annotations

from ..quality import build_improved_prompt, classify, explain, generate_prompt
from ..schemas.api import AssistantResponse


def analyse(raw: str, mode: str, business_function: str = "", task: str = "") -> AssistantResponse:
    analysis = classify(raw)

    if analysis.score == 0 and not raw.strip():
        return AssistantResponse(
            score=0,
            rating="Poor",
            breakdown=analysis.breakdown,
            missing=analysis.missing,
            present=[],
            recommendations=analysis.recommendations,
            improved_prompt="",
        )

    improved = ""
    generated = ""
    explanation = ""

    if mode == "improve":
        improved = build_improved_prompt(raw, analysis)
    elif mode == "generate":
        generated = generate_prompt(business_function, task or "ANALYSE", raw)
    elif mode == "explain":
        explanation = explain(raw, analysis)

    return AssistantResponse(
        score=analysis.score,
        rating=analysis.rating,
        breakdown=analysis.breakdown,
        missing=analysis.missing,
        present=analysis.present,
        recommendations=analysis.recommendations,
        analysis=[
            {"label": c.label, "status": "present" if c.present else "missing"}
            for c in analysis.components
        ],
        improved_prompt=improved,
        generated_prompt=generated,
        explanation=explanation,
    )

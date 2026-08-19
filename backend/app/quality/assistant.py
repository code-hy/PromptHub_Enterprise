"""Prompt Assistant service — analyse, improve, generate and explain prompts.

Deterministic by default so the demo behaves identically on any machine.
When an LLM is available, the provider augments generation; the quality
analysis itself is always rule-based.
"""

from __future__ import annotations

from .engine import PromptAnalysis

_PERSONA = "You are an experienced {role} working at Contoso Financial Services."

ROLES = {
    "FINANCE": "enterprise finance analyst",
    "HR": "senior HR business partner",
    "IT": "enterprise solutions architect",
    "LEGAL": "corporate counsel",
    "MARKETING": "marketing campaign manager",
    "OPERATIONS": "operations improvement lead",
    "PROJECT_MANAGEMENT": "programme management office advisor",
    "SALES": "sales enablement manager",
    "DATA_ANALYTICS": "enterprise data quality analyst",
    "EXECUTIVE": "management consultant",
    "RISK": "enterprise risk officer",
    "CUSTOMER_SERVICE": "customer experience manager",
    "GENERIC": "enterprise productivity advisor",
}

TASK_ACTIONS = {
    "ANALYSE": "Analyse",
    "CLASSIFY": "Classify",
    "CREATE": "Create",
    "EXTRACT": "Extract",
    "SUMMARISE": "Summarise",
    "COMPARE": "Compare",
    "TRANSFORM": "Transform",
    "REWRITE": "Rewrite",
    "TRANSLATE": "Translate",
    "RECOMMEND": "Recommend",
}


def build_improved_prompt(raw: str, analysis: PromptAnalysis) -> str:
    """Produce a structured, well-formed prompt from an imperfect one."""
    lines: list[str] = []
    has_verb = any(m in raw.lower() for m in GOAL_VERBS)
    core = raw.strip().rstrip(".")

    if analysis.score >= 85:
        return core

    lines.append(f"{core.capitalize() if not has_verb else core}.")

    if "Context" in analysis.missing:
        lines.append("")
        lines.append("Context:")
        lines.append(
            "The request is part of an enterprise working session and will be used to inform business decisions."
        )

    if "Source" in analysis.missing:
        lines.append("")
        lines.append("Source:")
        lines.append(
            "Use only the information supplied in the input material. Do not rely on general knowledge."
        )

    if "Expectations" in analysis.missing:
        lines.append("")
        lines.append("Expectations:")
        lines.append("1. Identify the most important findings")
        lines.append("2. Prioritise by business impact and urgency")
        lines.append("3. Be concise and actionable")

    if "Constraints" in analysis.missing:
        lines.append("")
        lines.append("Do not infer information that is not supported by the source material.")

    if "Audience" in analysis.missing:
        lines.append("")
        lines.append("This response is prepared for senior management review.")

    if "Output format" in analysis.missing:
        lines.append("")
        lines.append("Return the result as a structured summary with headings.")

    return "\n".join(lines)


def generate_prompt(business_function: str, task: str, topic: str = "") -> str:
    """Generate a complete structured prompt from scratch."""
    role = ROLES.get(business_function, ROLES["GENERIC"])
    action = TASK_ACTIONS.get(task, "Analyse")
    subject = topic.strip() or "the supplied information"

    return f"""{_PERSONA.format(role=role)}

Goal:
{action} {subject} and produce a clear, decision-ready summary.

Context:
{subject.capitalize()} will be used to support planning and management decisions at Contoso Financial Services.

Source:
Use only the supplied input material and any knowledge sources attached to this request.

Expectations:
1. Identify the most important facts and findings
2. Highlight risks, issues and required decisions
3. Recommend concrete next actions, each with an owner suggestion
4. Prioritise by business impact and urgency

Audience: Senior management
Output format: Structured summary with headings and a short recommendations list
Constraints: Do not invent information that is not present in the source material."""


def explain(raw: str, analysis: PromptAnalysis) -> str:
    """Explain why a prompt scored the way it did (educational mode)."""
    lines = [
        f"Your prompt scored **{analysis.score}/100** ({analysis.rating}).",
        "",
        "Here is what it did well:",
    ]
    if analysis.present:
        for item in analysis.present:
            lines.append(f"- Good: {item}")
    else:
        lines.append("- Nothing yet — it is too sparse to score well.")
    lines.append("")
    lines.append("What is missing:")
    for item in analysis.missing:
        lines.append(f"- Missing: {item}")
    lines.append("")
    lines.append("Why it matters: each component of a prompt controls one part of the")
    lines.append("answer quality — the AI cannot produce a targeted, grounded, formatted")
    lines.append("response unless the prompt tells it what to achieve, what to use, and")
    lines.append("how to present the result.")
    return "\n".join(lines)


GOAL_VERBS = {
    "summarise",
    "summarize",
    "analyse",
    "analyze",
    "classify",
    "extract",
    "create",
    "generate",
    "draft",
    "write",
    "rewrite",
    "translate",
    "compare",
    "transform",
    "recommend",
    "assess",
    "evaluate",
    "identify",
    "explain",
    "review",
    "produce",
}

"""Deterministic Prompt Quality Engine.

Scores a prompt on the nine-component rubric from the specification
(sections 15-16). The engine is intentionally rule-based so scores are
stable, explainable and testable without an LLM.

Score rubric (total 100):

    Goal              20
    Context           15
    Source            15
    Expectations      20
    Specificity       10
    Constraints        5
    Audience           5
    Output format      5
    Examples           5
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ComponentScore:
    label: str
    scored: int
    max: int
    present: bool
    evidence: str = ""


@dataclass
class PromptAnalysis:
    score: int
    rating: str
    breakdown: dict[str, dict[str, int]]
    present: list[str]
    missing: list[str]
    recommendations: list[str]
    components: list[ComponentScore] = field(default_factory=list)


# --- lexical classifiers -----------------------------------------------------

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
    "produce",
    "build",
    "design",
    "explain",
    "review",
    "determine",
    "calculate",
    "forecast",
    "prioritise",
    "prioritize",
    "convert",
    "outline",
    "plan",
    "develop",
    "prepare",
}

CONTEXT_MARKERS = [
    "context",
    "background",
    "for the",
    "in the context of",
    "this is",
    "the dataset",
    "the project",
    "the company",
    "the organisation",
    "the organization",
    "our team",
    "we are",
    "used to support",
    "audience is",
    "scenario",
    "situation",
]

SOURCE_MARKERS = [
    "source",
    "based on",
    "use only",
    "use the",
    "from the supplied",
    "using the",
    "from the following",
    "the attached",
    "the supplied",
    "refer to",
    "data provided",
    "documents",
    "dataset",
    "register",
    "notes",
    "emails",
    "report",
]

EXPECTATION_MARKERS = [
    "expect",
    "provide",
    "include",
    "output",
    "format",
    "structure",
    "return",
    "list",
    "table",
    "should",
    "must",
    "for each",
    "with the",
    "steps",
    "sections",
    "bullet",
    "columns",
    "recommendation",
    "severity",
    "evidence",
]

CONSTRAINT_MARKERS = [
    "do not",
    "don't",
    "must not",
    "avoid",
    "never",
    "only",
    "limit",
    "restrict",
    "without",
    "unless",
    "no more than",
    "do not invent",
    "do not infer",
]

AUDIENCE_MARKERS = [
    "executive",
    "senior management",
    "board",
    "management",
    "stakeholders",
    "audience",
    "team",
    "customer",
    "clients",
    "for the ceo",
    "for the cfo",
    "technical staff",
    "for project managers",
    "for developers",
    "non-technical",
]

OUTPUT_FORMAT_MARKERS = [
    "table",
    "bullet",
    "markdown",
    "json",
    "executive summary",
    "structured",
    "one page",
    "email",
    "memo",
    "report",
    "slide",
    "deck",
    "database schema",
    "ddl",
    "data dictionary",
    "csv",
    "list",
    "numbered",
    "format",
]

EXAMPLE_MARKERS = [
    "example",
    "for instance",
    "e.g.",
    "such as",
    "sample",
    "illustration",
    "example output",
]

SPECIFICITY_MARKERS = re.compile(
    r"\b\d+(\.\d+)?\b|specific|exactly|precisely|named|by name|the specific", re.IGNORECASE
)

_LENGTH_HINTS = {
    "concise": 0,
    "brief": 0,
    "summary": 0,
    "comprehensive": 1,
    "detailed": 1,
    "thorough": 1,
    "in depth": 1,
    "500 words": 1,
    "one page": 1,
    "no more than 500 words": 0,
}


def _has_any(text: str, markers: set[str] | list[str]) -> bool:
    lowered = text.lower()
    return any(m in lowered for m in markers)


def _count_any(text: str, markers: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for m in markers if m in lowered)


def classify(text: str) -> PromptAnalysis:
    """Analyse a single free-text prompt and produce component scores."""
    text = text.strip()
    words = len(text.split())
    if not text:
        return _empty_analysis()

    components: list[ComponentScore] = []

    # Goal (20)
    has_verb = _has_any(text, GOAL_VERBS)
    goal = 20 if has_verb else 0
    components.append(
        ComponentScore(
            "Goal",
            goal,
            20,
            has_verb,
            "Action verb(s) present" if has_verb else "No clear action verb",
        )
    )

    # Context (15)
    ctx_hits = _count_any(text, CONTEXT_MARKERS)
    context = min(15, 8 + ctx_hits * 4 if ctx_hits else 0)
    if ctx_hits == 0:
        context = 0
    components.append(
        ComponentScore(
            "Context",
            context,
            15,
            ctx_hits > 0,
            f"{ctx_hits} context marker(s)" if ctx_hits else "No context",
        )
    )

    # Source (15)
    src_hits = _count_any(text, SOURCE_MARKERS)
    source = min(15, 8 + src_hits * 4 if src_hits else 0)
    if src_hits == 0:
        source = 0
    components.append(
        ComponentScore(
            "Source",
            source,
            15,
            src_hits > 0,
            f"{src_hits} source marker(s)" if src_hits else "No source",
        )
    )

    # Expectations (20)
    exp_hits = _count_any(text, EXPECTATION_MARKERS)
    expectations = min(20, 8 + exp_hits * 4 if exp_hits else 0)
    if exp_hits == 0:
        expectations = 0
    components.append(
        ComponentScore(
            "Expectations", expectations, 20, exp_hits > 0, f"{exp_hits} expectation marker(s)"
        )
    )

    # Specificity (10)
    specific = 4 if words >= 60 else 0
    specific += 3 if SPECIFICITY_MARKERS.search(text) else 0
    specific += 3 if _has_any(text, _LENGTH_HINTS) else 0
    specific = min(10, specific)
    components.append(
        ComponentScore(
            "Specificity",
            specific,
            10,
            specific >= 5,
            "Length/detail signals" if specific >= 5 else "Generic",
        )
    )

    # Constraints (5)
    constraints = 5 if _has_any(text, CONSTRAINT_MARKERS) else 0
    components.append(
        ComponentScore(
            "Constraints",
            constraints,
            5,
            constraints > 0,
            "Constraint markers" if constraints else "No constraints",
        )
    )

    # Audience (5)
    audience = 5 if _has_any(text, AUDIENCE_MARKERS) else 0
    components.append(
        ComponentScore(
            "Audience",
            audience,
            5,
            audience > 0,
            "Audience identified" if audience else "No audience",
        )
    )

    # Output format (5)
    fmt = 5 if _has_any(text, OUTPUT_FORMAT_MARKERS) else 0
    components.append(
        ComponentScore(
            "Output format", fmt, 5, fmt > 0, "Format identified" if fmt else "No output format"
        )
    )

    # Examples (5)
    examples = 5 if _has_any(text, EXAMPLE_MARKERS) else 0
    components.append(
        ComponentScore(
            "Examples",
            examples,
            5,
            examples > 0,
            "Examples provided" if examples else "No examples",
        )
    )

    total = sum(c.scored for c in components)
    present = [c.label for c in components if c.present]
    missing = [c.label for c in components if not c.present]

    recommendations = _build_recommendations(missing, components)

    return PromptAnalysis(
        score=total,
        rating=rating_for(total),
        breakdown={
            c.label.lower().replace(" ", "_"): {"scored": c.scored, "max": c.max}
            for c in components
        },
        present=present,
        missing=missing,
        recommendations=recommendations,
        components=components,
    )


def _build_recommendations(missing: list[str], components: list[ComponentScore]) -> list[str]:
    recs = [
        ("Goal", "State clearly what the AI must accomplish (start with an action verb)."),
        ("Context", "Give the AI the background it needs to understand the task."),
        ("Source", "Name the authoritative information the AI should use."),
        ("Expectations", "Describe exactly how the answer should be produced."),
        ("Specificity", "Add concrete detail: named items, numbers or required length."),
        ("Constraints", "Tell the model what it must not do or infer."),
        ("Audience", "Specify who will consume the answer."),
        ("Output format", "Define the required structure for the answer."),
        ("Examples", "Provide an example of the kind of answer you want."),
    ]
    return [desc for label, desc in recs if label in missing]


def rating_for(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Needs improvement"
    return "Poor"


def analyse_prompt_fields(
    goal: str = "",
    context: str = "",
    source: str = "",
    expectations: str = "",
    audience: str = "",
    output_format: str = "",
    examples: str = "",
    constraints: str = "",
) -> PromptAnalysis:
    """Score a structured prompt (Prompt Builder form) instead of free text."""
    shared = "\n".join(
        p
        for p in (
            goal,
            context,
            source,
            expectations,
            audience,
            output_format,
            examples,
            constraints,
        )
        if p
    )

    components = []
    # Goal
    components.append(
        ComponentScore(
            "Goal", 20 if _has_any(goal, GOAL_VERBS) or goal.strip() else 0, 20, bool(goal.strip())
        )
    )
    # Context
    components.append(
        ComponentScore(
            "Context",
            min(15, 8 + _count_any(context, CONTEXT_MARKERS) * 4) if context.strip() else 0,
            15,
            bool(context.strip()),
        )
    )
    # Source
    components.append(
        ComponentScore(
            "Source",
            min(15, 8 + _count_any(source, SOURCE_MARKERS) * 4) if source.strip() else 0,
            15,
            bool(source.strip()),
        )
    )
    # Expectations
    components.append(
        ComponentScore(
            "Expectations",
            min(20, 8 + _count_any(expectations, EXPECTATION_MARKERS) * 4)
            if expectations.strip()
            else 0,
            20,
            bool(expectations.strip()),
        )
    )
    # Specificity
    spec = 4 if len(shared) >= 80 else 0
    spec += 3 if SPECIFICITY_MARKERS.search(shared) else 0
    spec += 3 if _has_any(shared, _LENGTH_HINTS) else 0
    components.append(ComponentScore("Specificity", min(10, spec), 10, spec >= 5))
    # Constraints
    components.append(
        ComponentScore(
            "Constraints",
            5 if _has_any(constraints, CONSTRAINT_MARKERS) or constraints.strip() else 0,
            5,
            bool(constraints.strip()),
        )
    )
    # Audience
    components.append(
        ComponentScore("Audience", 5 if audience.strip() else 0, 5, bool(audience.strip()))
    )
    # Output format
    components.append(
        ComponentScore(
            "Output format", 5 if output_format.strip() else 0, 5, bool(output_format.strip())
        )
    )
    # Examples
    components.append(
        ComponentScore("Examples", 5 if bool(examples.strip()) else 0, 5, bool(examples.strip()))
    )

    total = sum(c.scored for c in components)
    present = [c.label for c in components if c.present]
    missing = [c.label for c in components if not c.present]
    return PromptAnalysis(
        score=total,
        rating=rating_for(total),
        breakdown={
            c.label.lower().replace(" ", "_"): {"scored": c.scored, "max": c.max}
            for c in components
        },
        present=present,
        missing=missing,
        recommendations=_build_recommendations(missing, components),
        components=components,
    )


def _empty_analysis() -> PromptAnalysis:
    labels = [
        "Goal",
        "Context",
        "Source",
        "Expectations",
        "Specificity",
        "Constraints",
        "Audience",
        "Output format",
        "Examples",
    ]
    return PromptAnalysis(
        score=0,
        rating="Poor",
        breakdown={
            label.lower().replace(" ", "_"): {"scored": 0, "max": _MAXX.get(label, 5)}
            for label in labels
        },
        present=[],
        missing=labels,
        recommendations=[
            "Start by stating what you want the AI to achieve.",
            "Add context, source and expectations as you go.",
            "Use the Prompt Builder to structure the field-by-field.",
        ],
        components=[ComponentScore(label, 0, _MAXX.get(label, 5), False) for label in labels],
    )


_MAXX = {
    "Goal": 20,
    "Context": 15,
    "Source": 15,
    "Expectations": 20,
    "Specificity": 10,
    "Constraints": 5,
    "Audience": 5,
    "Output format": 5,
    "Examples": 5,
}

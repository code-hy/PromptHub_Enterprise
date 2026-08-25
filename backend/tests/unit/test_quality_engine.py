"""Tests for the deterministic quality engine rubric (spec 15-16)."""

from __future__ import annotations

from app.quality.engine import (
    analyse_prompt_fields,
    classify,
    rating_for,
)


def _strong_prompt() -> str:
    return (
        "Summarise the quarterly financial performance for the CEO."
        "Context: Contoso revenue was $18.4M against a $19.8M budget."
        "Source: use only the supplied profit and loss dataset."
        "Expectations: return a one-page executive summary with a table of"
        "budget vs actual variance, highlight the two largest variances, and"
        "do not invent figures not present in the data. Audience: executive."
    )


def test_classify_scores_full_rubric():
    analysis = classify(_strong_prompt())
    assert analysis.score >= 75, analysis.breakdown
    assert analysis.rating in ("Excellent", "Good")


def test_classify_empty_is_poor():
    analysis = classify("")
    assert analysis.score == 0
    assert analysis.rating == "Poor"
    assert len(analysis.missing) == 9


def test_goal_needs_action_verb():
    no_verb = classify("The quarterly report please.")
    assert no_verb.breakdown["goal"]["scored"] == 0


def test_rating_boundaries():
    assert rating_for(95) == "Excellent"
    assert rating_for(90) == "Excellent"
    assert rating_for(75) == "Good"
    assert rating_for(60) == "Needs improvement"
    assert rating_for(30) == "Poor"


def test_structured_fields_analysis():
    analysis = analyse_prompt_fields(
        goal="Draft a professional email requesting the budget contingency.",
        context="On behalf of the steering group for Project Atlas.",
        source="Use only the supplied budget figures.",
        expectations="Return a complete email with subject line and call to action.",
        audience="CFO",
        output_format="EMAIL",
    )
    assert analysis.breakdown["goal"]["max"] == 20
    assert analysis.breakdown["expectations"]["max"] == 20
    assert analysis.score >= 60


def test_structured_missing_fields_lose_points():
    bare = analyse_prompt_fields(goal="Draft an email")
    full = analyse_prompt_fields(
        goal="Draft an email requesting budget approval for the project costs.",
        context="Contoso must release contingency for the integration workstream.",
        source="Use only the supplied risk register and budget workbook.",
        expectations="Return an email with subject, three paragraphs and next steps.",
        audience="CFO",
        output_format="EMAIL",
    )
    assert bare.score < full.score

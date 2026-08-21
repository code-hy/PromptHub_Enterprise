"""Prompt execution service — runs a prompt through the LLM gateway,
records execution + evaluation + grounding/citations (spec 24, 44, 59-61)."""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from ..ids import next_execution_id
from ..llm import GroundingContext, get_provider
from ..models import Prompt, PromptExecution, User
from ..rag import LocalRetriever
from ..schemas.api import ExecutionOut, ExecutionRequest
from . import audit_service


def _resolve_prompt_template(prompt: Prompt, input_data: dict) -> str:
    """Fill {{variable}} placeholders in the prompt_template with input values."""
    template = prompt.prompt_template or "\n\n".join(
        p
        for p in (
            prompt.system_instruction,
            prompt.goal,
            prompt.context,
            prompt.source,
            prompt.expectations,
        )
        if p
    )
    if not template:
        template = prompt.goal or prompt.name

    def repl(match: re.Match) -> str:
        key = match.group(1).strip()
        value = input_data.get(key)
        if value is None:
            return match.group(0)
        if isinstance(value, (dict, list)):
            value = str(value)
        return str(value)

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", repl, template)


def run_prompt(
    db: Session,
    prompt: Prompt,
    user: User,
    req: ExecutionRequest,
) -> PromptExecution:

    provider = get_provider(req.model_provider, req.model_name)
    input_data = req.input_data or {}
    grounding_ctx = GroundingContext()

    if req.use_grounding or prompt.require_evidence:
        retriever = LocalRetriever(db)
        query = " ".join(
            str(v) for v in input_data.values() if isinstance(v, (str, int, float)) and str(v)
        ) or (prompt.goal or prompt.name)
        hits = retriever.retrieve(query, top_k=5, document_ids=req.document_ids or None)
        grounding_ctx.chunks = hits
        grounding_ctx.sources = [h["name"] for h in hits]
        grounding_ctx.evidence = [
            {"document_id": h["document_id"], "name": h["name"], "snippet": h["snippet"]}
            for h in hits
        ]

    prompt_text = _resolve_prompt_template(prompt, input_data)
    result = provider.generate(
        prompt_text,
        system=prompt.system_instruction or prompt.goal or "",
        temperature=req.temperature if req.temperature is not None else prompt.temperature,
        grounding=grounding_ctx,
        task_hint=prompt.task,
        output_format_hint=prompt.output_format,
    )

    eval_metrics = evaluate_output(result.output, prompt, grounding_ctx)

    execution = PromptExecution(
        execution_id=next_execution_id(db),
        prompt_id=prompt.id,
        version=prompt.version,
        user_id=user.id,
        provider=result.provider,
        model=result.model,
        temperature=req.temperature if req.temperature is not None else prompt.temperature,
        input_data=input_data,
        output=result.output,
        status="SUCCESS",
        tokens=result.tokens,
        latency_ms=result.latency_ms,
        sources_used=grounding_ctx.sources,
        evidence=grounding_ctx.evidence,
        eval_metrics=eval_metrics,
        execution_mode="PROMPT",
    )
    db.add(execution)
    db.flush()
    audit_service.record(
        db,
        "PROMPT_EXECUTED",
        user,
        entity_type="PROMPT",
        entity_ref=prompt.prompt_id,
        entity_name=prompt.name,
        details={
            "provider": result.provider,
            "model": result.model,
            "latency_ms": result.latency_ms,
        },
    )
    db.commit()
    db.refresh(execution)
    return execution


def evaluate_output(output: str, prompt: Prompt, grounding: GroundingContext) -> dict:
    """Deterministic evaluation heuristics (spec 59-60). AI-generated, human review
    recommended."""
    lowered = output.lower()
    word_count = len(output.split())

    # Instruction adherence: did the output include expected section markers?
    expected_markers = ["##", "###"]
    instruction = min(100, 55 + 15 * sum(1 for m in expected_markers if m in lowered))
    if len(prompt.expectations) > 40 and "**" in output:
        instruction = min(100, instruction + 10)

    # Grounding: output cites sources when grounding present
    grounding_score = 70.0
    if grounding and grounding.sources:
        grounding_score = min(
            100, 65 + 10 * sum(1 for s in grounding.sources if s.lower()[:12] in lowered)
        )
        if "evidence" in lowered or "source" in lowered or "**" in lowered:
            grounding_score = min(100, grounding_score + 10)

    # Completeness: length + structure
    completeness = min(100, 40 + word_count // 8)
    if any(c in lowered for c in ["1.", "2.", "3.", "|", "- "]):
        completeness = min(100, completeness + 15)

    # Consistency: presence of a conclusion
    consistency = (
        82.0
        if any(w in lowered for w in ["**note:**", "summary", "findings", "conclusion", "analysis"])
        else 70.0
    )

    # Relevance: output roughly matches the prompt's goal keywords
    goal_keywords = set(re.findall(r"[a-z]{4,}", prompt.goal.lower())) if prompt.goal else set()
    if goal_keywords:
        matched = sum(1 for kw in goal_keywords if kw in lowered)
        relevance = min(100, 55 + matched * 8)
    else:
        relevance = 80.0

    # Safety: check for disallowed patterns e.g. overly sensitive claims
    safety = 95.0
    disallowed = [
        "however, i cannot",
        "the model does not",
        "as an ai, i",
        "i'm sorry",
    ]
    if any(d in lowered for d in disallowed):
        safety = 60.0

    # Format score: matches requested output format
    fmt = 85.0
    wanted = (prompt.output_format or "").lower()
    if "table" in wanted and "|" in output:
        fmt = 95.0
    elif "bullet" in wanted and "- " in output:
        fmt = 95.0
    elif "summary" in wanted and ("##" in output or "summary" in lowered):
        fmt = 95.0

    overall = round(
        0.2 * instruction
        + 0.2 * grounding_score
        + 0.2 * completeness
        + 0.15 * consistency
        + 0.15 * relevance
        + 0.05 * safety
        + 0.05 * fmt,
        1,
    )
    return {
        "instruction_score": round(instruction, 1),
        "grounding_score": round(grounding_score, 1),
        "completeness_score": round(completeness, 1),
        "consistency_score": round(consistency, 1),
        "relevance_score": round(relevance, 1),
        "safety_score": round(safety, 1),
        "format_score": round(fmt, 1),
        "overall_score": overall,
        "is_ai_generated": True,
        "grade": _grade(overall),
    }


def _grade(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Needs improvement"
    return "Poor"


def list_executions(
    db: Session,
    *,
    prompt_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
) -> tuple[list[PromptExecution], int]:
    query = db.query(PromptExecution)
    if prompt_id is not None:
        query = query.filter(PromptExecution.prompt_id == prompt_id)
    if status:
        query = query.filter(PromptExecution.status == status)
    total = query.count()
    items = query.order_by(PromptExecution.created_at.desc()).limit(limit).offset(offset).all()
    return items, total


def to_execution_out(db: Session, ex: PromptExecution) -> ExecutionOut:
    prompt = db.get(Prompt, ex.prompt_id)
    time_saved = 0.0
    if prompt:
        time_saved = max(0.0, prompt.manual_time_minutes - prompt.ai_time_minutes)
    return ExecutionOut(
        id=ex.id,
        execution_id=ex.execution_id,
        prompt_id=ex.prompt_id,
        version=ex.version,
        provider=ex.provider,
        model=ex.model,
        status=ex.status,
        input_data=ex.input_data or {},
        output=ex.output,
        tokens=ex.tokens,
        latency_ms=ex.latency_ms,
        sources_used=ex.sources_used or [],
        evidence=ex.evidence or [],
        eval_metrics=ex.eval_metrics or {},
        error_message=ex.error_message,
        estimated_time_saved_minutes=round(time_saved, 1),
        created_at=ex.created_at,
    )

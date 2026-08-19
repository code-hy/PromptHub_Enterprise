"""Workflow / promptbook service — sequential prompt execution where each
step builds on the previous response (spec 25-27, 45)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ids import next_workflow_execution_id, next_workflow_id
from ..llm import GroundingContext, get_provider
from ..models import (
    Prompt,
    User,
    Workflow,
    WorkflowExecution,
    WorkflowStep,
)
from ..rag import LocalRetriever
from ..schemas.api import (
    WorkflowCreate,
    WorkflowExecutionOut,
    WorkflowOut,
    WorkflowRunRequest,
)
from . import audit_service


def create_workflow(db: Session, data: WorkflowCreate, user: User) -> Workflow:
    wf = Workflow(
        workflow_id=next_workflow_id(db),
        name=data.name,
        description=data.description,
        status="DRAFT",
        owner_id=user.id,
        business_function=data.business_function,
        tags=data.tags or [],
    )
    db.add(wf)
    db.flush()
    for idx, step in enumerate(data.steps, start=1):
        prompt = db.get(Prompt, step.prompt_id)
        wf.steps.append(
            WorkflowStep(
                workflow_id=wf.id,
                step_id=f"STEP-{idx:03d}",
                sequence=step.sequence or idx,
                name=step.name or (prompt.name if prompt else ""),
                prompt_id=step.prompt_id,
                input_mapping=step.input_mapping or {},
                continue_on_failure=step.continue_on_failure,
            )
        )
    audit_service.record(
        db,
        "WORKFLOW_CREATED",
        user,
        entity_type="WORKFLOW",
        entity_ref=wf.workflow_id,
        entity_name=wf.name,
    )
    db.commit()
    db.refresh(wf)
    return wf


def list_workflows(db: Session) -> tuple[list[Workflow], int]:
    items = db.query(Workflow).order_by(Workflow.updated_at.desc()).all()
    return items, len(items)


def get_workflow(db: Session, workflow_id_ref: str | int) -> Workflow | None:
    stmt = select(Workflow)
    if isinstance(workflow_id_ref, int) or str(workflow_id_ref).isdigit():
        stmt = stmt.where(Workflow.id == int(workflow_id_ref))
    else:
        stmt = stmt.where(Workflow.workflow_id == workflow_id_ref)
    return db.scalar(stmt)


def _resolve_input(
    mapping: dict, input_data: dict, step_results: list[dict], defaults: dict
) -> dict:
    """Resolve {{step_N.output}} / {{input.field}} placeholders in step mappings."""
    resolved: dict[str, Any] = {}

    def lookup(key: str):
        meta = re.fullmatch(r"step_(\d+)\.output", key)
        if meta:
            idx = int(meta.group(1)) - 1
            if 0 <= idx < len(step_results) and step_results[idx].get("status") == "SUCCESS":
                return step_results[idx].get("output", "")
            return ""
        if key.startswith("input."):
            return input_data.get(key.split(".", 1)[1])
        if key in defaults:
            return defaults[key]
        return input_data.get(key)

    for target, source in (mapping or {}).items():
        resolved[target] = lookup(source)
    return resolved


def run_workflow(
    db: Session,
    wf: Workflow,
    user: User,
    req: WorkflowRunRequest,
) -> WorkflowExecution:
    provider = get_provider()
    retriever = LocalRetriever(db)
    input_data = req.input_data or {}
    document_ids = req.document_ids or []
    started = datetime.now(UTC)

    wf_exec = WorkflowExecution(
        execution_id=next_workflow_execution_id(db),
        workflow_id=wf.id,
        workflow_name=wf.name,
        user_id=user.id,
        status="RUNNING",
        inputs=input_data,
        step_results=[],
    )
    db.add(wf_exec)
    db.commit()

    step_results: list[dict] = []
    all_sources: list[str] = []
    final_output = ""
    failed = False

    steps = sorted(wf.steps, key=lambda s: s.sequence)
    for step in steps:
        prompt = db.get(Prompt, step.prompt_id)
        if prompt is None:
            step_results.append(
                {
                    "step_id": step.step_id,
                    "sequence": step.sequence,
                    "name": step.name,
                    "status": "FAILED",
                    "error": "Prompt not found",
                }
            )
            if not step.continue_on_failure:
                failed = True
                break
            continue

        resolved = _resolve_input(step.input_mapping, input_data, step_results, req.input_data)

        grounding = GroundingContext()
        query_txt = (
            " ".join(str(v) for v in resolved.values() if isinstance(v, str))
            or prompt.goal
            or prompt.name
        )
        hits = retriever.retrieve(query_txt, top_k=4, document_ids=document_ids or None)
        grounding.chunks = hits
        grounding.sources = [h["name"] for h in hits]

        template = prompt.prompt_template or prompt.goal or prompt.name
        step_prompt = re.sub(
            r"\{\{\s*(\w+)\s*\}\}",
            lambda m: str(resolved.get(m.group(1), m.group(0))),
            template,
        )

        try:
            result = provider.generate(
                step_prompt,
                system=prompt.system_instruction or prompt.goal or "",
                temperature=prompt.temperature,
                grounding=grounding,
                task_hint=prompt.task,
                output_format_hint=prompt.output_format,
            )
            step_results.append(
                {
                    "step_id": step.step_id,
                    "sequence": step.sequence,
                    "name": step.name,
                    "prompt_id": prompt.prompt_id,
                    "prompt_name": prompt.name,
                    "status": "SUCCESS",
                    "output": result.output,
                    "model": result.model,
                    "provider": result.provider,
                    "tokens": result.tokens,
                    "latency_ms": result.latency_ms,
                    "sources": grounding.sources,
                    "evidence": grounding.evidence,
                }
            )
            all_sources.extend(grounding.sources)
            final_output = result.output
        except Exception as exc:  # pragma: no cover - provider fallbacks mask most failures
            step_results.append(
                {
                    "step_id": step.step_id,
                    "sequence": step.sequence,
                    "name": step.name,
                    "status": "FAILED",
                    "error": str(exc),
                }
            )
            if not step.continue_on_failure:
                failed = True
                break

    wf_exec.step_results = step_results
    wf_exec.final_output = final_output
    wf_exec.sources_used = list(dict.fromkeys(all_sources))
    wf_exec.status = "FAILED" if failed else "SUCCESS"
    wf_exec.latency_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)
    wf_exec.ended_at = datetime.now(UTC)
    db.commit()
    db.refresh(wf_exec)

    audit_service.record(
        db,
        "WORKFLOW_EXECUTED",
        user,
        entity_type="WORKFLOW",
        entity_ref=wf.workflow_id,
        entity_name=wf.name,
        details={"status": wf_exec.status, "steps": len(step_results)},
    )
    db.commit()
    db.refresh(wf_exec)
    return wf_exec


def to_workflow_out(wf: Workflow) -> WorkflowOut:
    steps = []
    for s in sorted(wf.steps, key=lambda x: x.sequence):
        steps.append(
            {
                "id": s.id,
                "step_id": s.step_id,
                "sequence": s.sequence,
                "name": s.name,
                "prompt_id": s.prompt_id,
                "prompt_name": s.name,
                "input_mapping": s.input_mapping or {},
                "continue_on_failure": s.continue_on_failure,
            }
        )
    return WorkflowOut(
        id=wf.id,
        workflow_id=wf.workflow_id,
        name=wf.name,
        description=wf.description,
        status=wf.status,
        business_function=wf.business_function,
        tags=wf.tags or [],
        owner_id=wf.owner_id,
        steps=steps,
        estimated_manual_minutes=wf.estimated_manual_minutes,
        estimated_ai_minutes=wf.estimated_ai_minutes,
        created_at=wf.created_at,
    )


def to_workflow_execution_out(ex: WorkflowExecution) -> WorkflowExecutionOut:
    return WorkflowExecutionOut(
        id=ex.id,
        workflow_id=ex.workflow_id,
        execution_id=ex.execution_id,
        workflow_name=ex.workflow_name,
        status=ex.status,
        inputs=ex.inputs or {},
        step_results=ex.step_results or [],
        final_output=ex.final_output,
        sources_used=ex.sources_used or [],
        latency_ms=ex.latency_ms,
        error_message=ex.error_message,
        created_at=ex.created_at,
        ended_at=ex.ended_at,
    )

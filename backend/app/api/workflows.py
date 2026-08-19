"""Workflow / promptbook API (spec 45)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Workflow
from ..schemas.api import (
    WorkflowCreate,
    WorkflowExecutionOut,
    WorkflowListResponse,
    WorkflowOut,
    WorkflowRunRequest,
)
from ..security import get_current_user
from ..services import workflow_service

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=WorkflowListResponse)
def list_workflows(db: Session = Depends(get_db)):
    items, total = workflow_service.list_workflows(db)
    return WorkflowListResponse(
        items=[workflow_service.to_workflow_out(w) for w in items], total=total
    )


@router.post("", response_model=WorkflowOut)
def create_workflow(
    data: WorkflowCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    wf = workflow_service.create_workflow(db, data, user)
    return workflow_service.to_workflow_out(wf)


def _get_workflow_or_404(db: Session, ref: str) -> Workflow:
    wf = workflow_service.get_workflow(db, ref)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.get("/{workflow_ref}", response_model=WorkflowOut)
def get_workflow(workflow_ref: str, db: Session = Depends(get_db)):
    return workflow_service.to_workflow_out(_get_workflow_or_404(db, workflow_ref))


@router.post("/{workflow_ref}/run", response_model=WorkflowExecutionOut)
def run_workflow(
    workflow_ref: str,
    data: WorkflowRunRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wf = _get_workflow_or_404(db, workflow_ref)
    execution = workflow_service.run_workflow(db, wf, user, data)
    return workflow_service.to_workflow_execution_out(execution)


@router.get("/{workflow_ref}/executions")
def list_workflow_executions(workflow_ref: str, db: Session = Depends(get_db)):
    from ..models import WorkflowExecution

    wf = _get_workflow_or_404(db, workflow_ref)
    items = (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.workflow_id == wf.id)
        .order_by(WorkflowExecution.created_at.desc())
        .limit(20)
        .all()
    )
    return {"items": [workflow_service.to_workflow_execution_out(e) for e in items]}

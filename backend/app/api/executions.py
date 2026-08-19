"""Prompt execution API (spec 44)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Prompt, User
from ..schemas.api import ExecutionOut, ExecutionRequest
from ..security import get_current_user
from ..services import execution_service

router = APIRouter(prefix="/executions", tags=["executions"])


@router.post("", response_model=ExecutionOut)
def create_execution(
    data: ExecutionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = db.get(Prompt, data.prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    execution = execution_service.run_prompt(db, prompt, user, data)
    return execution_service.to_execution_out(db, execution)


@router.get("", response_model=dict)
def list_executions(
    prompt_id: int | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = execution_service.list_executions(
        db, prompt_id=prompt_id, limit=limit, offset=offset, status=status
    )
    return {"items": [execution_service.to_execution_out(db, e) for e in items], "total": total}


@router.get("/{execution_id}", response_model=ExecutionOut)
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    from ..models import PromptExecution

    execution = (
        db.query(PromptExecution).filter(PromptExecution.execution_id == execution_id).first()
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution_service.to_execution_out(db, execution)

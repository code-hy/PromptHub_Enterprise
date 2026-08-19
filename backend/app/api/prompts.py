"""Prompts, versions, ratings, favourites and lifecycle API (spec 41-42)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Prompt, User
from ..schemas.api import (
    CloneCreate,
    PromptCreate,
    PromptDetail,
    PromptFlowAction,
    PromptListResponse,
    PromptUpdate,
    RatingCreate,
    RatingOut,
    VersionCompare,
    VersionDetail,
    VersionOut,
)
from ..security import get_current_user, require_role
from ..services import lifecycle_service, prompt_service
from ..services.governance_service import evaluate_prompt_governance

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=PromptListResponse)
def list_prompts(
    search: str = "",
    business_function: str | None = None,
    application: str | None = None,
    task: str | None = None,
    status: str | None = None,
    risk_level: str | None = None,
    classification: str | None = None,
    tag: str | None = None,
    favourite_only: bool = False,
    is_template: bool | None = None,
    sort: str = "updated",
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return prompt_service.list_prompts(
        db,
        search=search,
        business_function=business_function,
        application=application,
        task=task,
        status=status,
        risk_level=risk_level,
        classification=classification,
        tag=tag,
        favourite_only=favourite_only,
        user_id=user.id,
        is_template=is_template,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=PromptDetail)
def create_prompt(
    data: PromptCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    prompt = prompt_service.create_prompt(db, data, user)
    return prompt_service.to_detail(prompt, db, user.id)


def _get_prompt_or_404(db: Session, ref: str) -> Prompt:
    prompt = prompt_service.get_prompt(db, ref)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.get("/{prompt_ref}", response_model=PromptDetail)
def get_prompt(
    prompt_ref: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    prompt = _get_prompt_or_404(db, prompt_ref)
    return prompt_service.to_detail(prompt, db, user.id)


@router.put("/{prompt_ref}", response_model=PromptDetail)
def update_prompt(
    prompt_ref: str,
    data: PromptUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = _get_prompt_or_404(db, prompt_ref)
    create_version = data.changes and prompt.status in ("PUBLISHED", "APPROVED")
    updated = prompt_service.update_prompt(db, prompt, data, user, create_version=create_version)
    return prompt_service.to_detail(updated, db, user.id)


@router.delete("/{prompt_ref}")
def delete_prompt(
    prompt_ref: str, db: Session = Depends(get_db), user: User = Depends(require_role("ADMIN"))
):
    prompt = _get_prompt_or_404(db, prompt_ref)
    db.delete(prompt)
    from ..services import audit_service

    audit_service.record(
        db,
        "PROMPT_DELETED",
        user,
        entity_type="PROMPT",
        entity_ref=prompt.prompt_id,
        entity_name=prompt.name,
    )
    db.commit()
    return {"ok": True}


@router.post("/{prompt_ref}/clone", response_model=PromptDetail)
def clone_prompt(
    prompt_ref: str,
    data: CloneCreate | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = _get_prompt_or_404(db, prompt_ref)
    cloned = prompt_service.clone_prompt(db, prompt, user, name=data.name if data else None)
    return prompt_service.to_detail(cloned, db, user.id)


@router.post("/{prompt_ref}/flow", response_model=PromptDetail)
def prompt_flow(
    prompt_ref: str,
    data: PromptFlowAction,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = _get_prompt_or_404(db, prompt_ref)
    action = data.action.lower()
    if action == "submit_for_review":
        result = lifecycle_service.submit_for_review(db, prompt, user, data.note)
    elif action == "approve":
        result = lifecycle_service.approve(db, prompt, user, data.note)
    elif action == "reject":
        result = lifecycle_service.reject(db, prompt, user, data.note)
    elif action == "publish":
        result = lifecycle_service.publish(db, prompt, user, data.note)
    elif action == "deprecate":
        result = lifecycle_service.deprecate(db, prompt, user, data.note)
    elif action == "retire":
        result = lifecycle_service.retire(db, prompt, user, data.note)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    return prompt_service.to_detail(result, db, user.id)


@router.post("/{prompt_ref}/rate", response_model=RatingOut)
def rate_prompt(
    prompt_ref: str,
    data: RatingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = _get_prompt_or_404(db, prompt_ref)
    rating = prompt_service.rate_prompt(db, prompt, user, data)
    return rating


@router.post("/{prompt_ref}/favourite")
def favourite_prompt(
    prompt_ref: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    prompt = _get_prompt_or_404(db, prompt_ref)
    is_fav = prompt_service.toggle_favourite(db, prompt, user)
    return {"is_favourite": is_fav}


@router.get("/{prompt_ref}/governance")
def prompt_governance(
    prompt_ref: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    prompt = _get_prompt_or_404(db, prompt_ref)
    result = evaluate_prompt_governance(db, prompt, actor=user)
    return {
        "prompt_id": prompt.prompt_id,
        "approved": result.approved,
        "violations": result.violations,
        "decisions": result.decisions,
    }


# ---------------------------------------------------------------------------
# Versions (spec 42)
# ---------------------------------------------------------------------------


@router.get("/{prompt_ref}/versions", response_model=list[VersionOut])
def list_versions(prompt_ref: str, db: Session = Depends(get_db)):
    prompt = _get_prompt_or_404(db, prompt_ref)
    return prompt_service.list_versions(db, prompt)


@router.get("/{prompt_ref}/versions/{version_ref}", response_model=VersionDetail)
def get_version(prompt_ref: str, version_ref: str, db: Session = Depends(get_db)):
    prompt = _get_prompt_or_404(db, prompt_ref)
    version = prompt_service.get_version(db, prompt, version_ref)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.get("/{prompt_ref}/compare", response_model=VersionCompare)
def compare_versions(
    prompt_ref: str,
    from_version: str,
    to_version: str,
    db: Session = Depends(get_db),
):
    prompt = _get_prompt_or_404(db, prompt_ref)
    old = prompt_service.get_version(db, prompt, from_version)
    new = prompt_service.get_version(db, prompt, to_version)
    changes = prompt_service.compare_versions(old, new)
    return VersionCompare(from_version=from_version, to_version=to_version, changes=changes)

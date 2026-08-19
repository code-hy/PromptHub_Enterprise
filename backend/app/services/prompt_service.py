"""Prompt CRUD, versioning, lifecycle, cloning, ratings and favourites."""

from __future__ import annotations

from typing import Any

from sqlalchemy import String, func, or_, select
from sqlalchemy.orm import Session, joinedload

from ..ids import next_prompt_id, next_user_id
from ..models import (
    Prompt,
    PromptExecution,
    PromptFavourite,
    PromptInput,
    PromptRating,
    PromptVersion,
    User,
)
from ..quality.engine import analyse_prompt_fields
from ..schemas.api import (
    PromptCreate,
    PromptDetail,
    PromptListResponse,
    PromptSummary,
    PromptUpdate,
    RatingCreate,
)
from . import audit_service


def _rating_stats(db: Session, prompt_id: int) -> tuple[float, int]:
    row = db.execute(
        select(
            func.avg(PromptRating.stars).label("avg"),
            func.count(PromptRating.id).label("cnt"),
        ).where(PromptRating.prompt_id == prompt_id)
    ).one()
    return (row.avg or 0.0, row.cnt or 0)


def _execution_count(db: Session, prompt_id: int) -> int:
    return (
        db.scalar(
            select(func.count(PromptExecution.id)).where(PromptExecution.prompt_id == prompt_id)
        )
        or 0
    )


def _is_favourite(db: Session, prompt_id: int, user_id: int | None) -> bool:
    if user_id is None:
        return False
    return (
        db.scalar(
            select(PromptFavourite.id).where(
                PromptFavourite.prompt_id == prompt_id,
                PromptFavourite.user_id == user_id,
            )
        )
        is not None
    )


def to_summary(prompt: Prompt, db: Session, user_id: int | None = None) -> PromptSummary:
    avg, cnt = _rating_stats(db, prompt.id)
    return PromptSummary(
        id=prompt.id,
        prompt_id=prompt.prompt_id,
        name=prompt.name,
        description=prompt.description,
        status=prompt.status,
        version=prompt.version,
        business_function=prompt.business_function,
        application=prompt.application,
        task=prompt.task,
        owner_id=prompt.owner_id,
        data_classification=prompt.data_classification,
        risk_level=prompt.risk_level,
        tags=prompt.tags or [],
        rating_avg=round(avg, 1),
        rating_count=cnt,
        execution_count=_execution_count(db, prompt.id),
        is_favourite=_is_favourite(db, prompt.id, user_id),
    )


def to_detail(prompt: Prompt, db: Session, user_id: int | None = None) -> PromptDetail:
    avg, cnt = _rating_stats(db, prompt.id)
    owner_name = ""
    owner = db.get(User, prompt.owner_id)
    if owner:
        owner_name = owner.display_name
    return PromptDetail(
        id=prompt.id,
        prompt_id=prompt.prompt_id,
        name=prompt.name,
        description=prompt.description,
        status=prompt.status,
        version=prompt.version,
        business_function=prompt.business_function,
        application=prompt.application,
        task=prompt.task,
        owner_id=prompt.owner_id,
        owner_name=owner_name,
        data_classification=prompt.data_classification,
        risk_level=prompt.risk_level,
        tags=prompt.tags or [],
        rating_avg=round(avg, 1),
        rating_count=cnt,
        execution_count=_execution_count(db, prompt.id),
        is_favourite=_is_favourite(db, prompt.id, user_id),
        goal=prompt.goal,
        context=prompt.context,
        source=prompt.source,
        expectations=prompt.expectations,
        system_instruction=prompt.system_instruction,
        prompt_template=prompt.prompt_template,
        audience=prompt.audience,
        tone=prompt.tone,
        output_format=prompt.output_format,
        max_length=prompt.max_length,
        contains_pii=prompt.contains_pii,
        contains_financial_data=prompt.contains_financial_data,
        contains_customer_data=prompt.contains_customer_data,
        external_sharing=prompt.external_sharing,
        requires_approval=prompt.requires_approval,
        temperature=prompt.temperature,
        require_evidence=prompt.require_evidence,
        avoid_unsupported_claims=prompt.avoid_unsupported_claims,
        ask_clarification_questions=prompt.ask_clarification_questions,
        manual_time_minutes=prompt.manual_time_minutes,
        ai_time_minutes=prompt.ai_time_minutes,
        quality_score=prompt.quality_score,
        inputs=[
            {
                "id": i.id,
                "name": i.name,
                "input_type": i.input_type,
                "required": i.required,
                "description": i.description,
                "sample_value": i.sample_value,
                "position": i.position,
            }
            for i in (prompt.inputs or [])
        ],
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        published_at=prompt.published_at,
    )


def list_prompts(
    db: Session,
    *,
    search: str = "",
    business_function: str | None = None,
    application: str | None = None,
    task: str | None = None,
    status: str | None = None,
    risk_level: str | None = None,
    classification: str | None = None,
    tag: str | None = None,
    favourite_only: bool = False,
    user_id: int | None = None,
    is_template: bool | None = None,
    sort: str = "updated",
    page: int = 1,
    page_size: int = 24,
) -> PromptListResponse:
    query = db.query(Prompt)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Prompt.name).like(like),
                func.lower(Prompt.description).like(like),
                func.lower(Prompt.goal).like(like),
                func.cast(Prompt.tags, String).ilike(like),
            )
        )
    if business_function:
        query = query.filter(Prompt.business_function == business_function)
    if application:
        query = query.filter(Prompt.application == application)
    if task:
        query = query.filter(Prompt.task == task)
    if status:
        query = query.filter(Prompt.status == status)
    if risk_level:
        query = query.filter(Prompt.risk_level == risk_level)
    if classification:
        query = query.filter(Prompt.data_classification == classification)
    if tag:
        query = query.filter(Prompt.tags.contains([tag]))
    if favourite_only and user_id:
        query = query.filter(
            Prompt.id.in_(
                select(PromptFavourite.prompt_id).where(PromptFavourite.user_id == user_id)
            )
        )
    if is_template is not None:
        query = query.filter(Prompt.is_template == is_template)

    if sort in ("rating", "executions"):
        join_col = (
            func.avg(PromptRating.stars) if sort == "rating" else func.count(PromptExecution.id)
        )
        query = (
            query.outerjoin(PromptRating) if sort == "rating" else query.outerjoin(PromptExecution)
        )
        query = query.group_by(Prompt.id).order_by(join_col.desc())
    else:
        sort_map = {
            "updated": Prompt.updated_at.desc(),
            "created": Prompt.created_at.desc(),
            "name": Prompt.name.asc(),
        }
        query = query.order_by(sort_map.get(sort, Prompt.updated_at.desc()))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PromptListResponse(
        items=[to_summary(p, db, user_id) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_prompt(db: Session, prompt_id_ref: str | int) -> Prompt | None:
    stmt = select(Prompt).options(
        joinedload(Prompt.inputs),
        joinedload(Prompt.versions),
    )
    if isinstance(prompt_id_ref, int) or str(prompt_id_ref).isdigit():
        stmt = stmt.where(Prompt.id == int(prompt_id_ref))
    else:
        stmt = stmt.where(Prompt.prompt_id == prompt_id_ref)
    return db.scalar(stmt)


def _set_inputs(prompt: Prompt, inputs: list[dict] | None, db: Session) -> None:
    if inputs is None:
        return
    prompt.inputs.clear()
    for position, item in enumerate(inputs):
        prompt.inputs.append(
            PromptInput(
                prompt_id=prompt.id,
                name=item.get("name", ""),
                input_type=item.get("input_type", "TEXT"),
                required=item.get("required", True),
                description=item.get("description", ""),
                sample_value=item.get("sample_value", ""),
                position=position,
            )
        )


def create_prompt(db: Session, data: PromptCreate, user: User) -> Prompt:
    analysis = analyse_prompt_fields(
        goal=data.goal,
        context=data.context,
        source=data.source,
        expectations=data.expectations,
        audience=data.audience,
        output_format=data.output_format,
    )
    prompt = Prompt(
        prompt_id=next_prompt_id(db),
        name=data.name,
        description=data.description,
        status="DRAFT",
        version="1.0",
        version_number=1,
        owner_id=user.id,
        business_function=data.business_function,
        application=data.application,
        task=data.task,
        goal=data.goal,
        context=data.context,
        source=data.source,
        expectations=data.expectations,
        system_instruction=data.system_instruction,
        prompt_template=data.prompt_template,
        audience=data.audience,
        tone=data.tone,
        output_format=data.output_format,
        max_length=data.max_length,
        data_classification=data.data_classification,
        risk_level=data.risk_level,
        requires_approval=data.risk_level in ("HIGH", "CRITICAL")
        or data.data_classification == "RESTRICTED",
        contains_pii=data.contains_pii,
        contains_financial_data=data.contains_financial_data,
        contains_customer_data=data.contains_customer_data,
        external_sharing=data.external_sharing,
        temperature=data.temperature,
        require_evidence=data.require_evidence,
        avoid_unsupported_claims=data.avoid_unsupported_claims,
        ask_clarification_questions=data.ask_clarification_questions,
        manual_time_minutes=data.manual_time_minutes,
        ai_time_minutes=data.ai_time_minutes,
        tags=data.tags or [],
        quality_score=analysis.score,
    )
    db.add(prompt)
    db.flush()
    _set_inputs(prompt, [i.model_dump() for i in data.inputs], db)
    db.flush()
    prompt.versions.append(
        PromptVersion(
            prompt_id=prompt.id,
            version="1.0",
            version_number=1,
            author_id=user.id,
            changes="Initial version",
            snapshot=_snapshot(prompt),
        )
    )
    audit_service.record(
        db,
        "PROMPT_CREATED",
        user,
        entity_type="PROMPT",
        entity_ref=prompt.prompt_id,
        entity_name=prompt.name,
        details={"quality_score": analysis.score},
    )
    db.commit()
    db.refresh(prompt)
    return prompt


def update_prompt(
    db: Session,
    prompt: Prompt,
    data: PromptUpdate,
    user: User,
    *,
    create_version: bool = False,
) -> Prompt:
    changes: list[str] = []
    fields = data.model_dump(exclude_unset=True)
    changes_text = data.changes or ""

    for key, value in fields.items():
        if key == "inputs":
            continue
        if not hasattr(prompt, key):
            continue
        old = getattr(prompt, key)
        if old != value:
            changes.append(f"{key} changed")
            setattr(prompt, key, value)

    analysis = analyse_prompt_fields(
        goal=prompt.goal,
        context=prompt.context,
        source=prompt.source,
        expectations=prompt.expectations,
        audience=prompt.audience,
        output_format=prompt.output_format,
    )
    prompt.quality_score = analysis.score

    if "inputs" in fields and fields["inputs"] is not None:
        _set_inputs(
            prompt,
            [
                {
                    "name": i.name,
                    "input_type": i.input_type,
                    "required": i.required,
                    "description": i.description,
                    "sample_value": i.sample_value,
                }
                for i in fields["inputs"]
            ],
            db,
        )

    db.flush()
    if create_version and changes:
        new_number = prompt.version_number + 1
        prompt.version_number = new_number
        prompt.version = _version_label(new_number)
        summary = changes_text or "; ".join(changes)
        prompt.versions.append(
            PromptVersion(
                prompt_id=prompt.id,
                version=prompt.version,
                version_number=new_number,
                author_id=user.id,
                changes=summary,
                snapshot=_snapshot(prompt),
            )
        )
        audit_service.record(
            db,
            "PROMPT_VERSIONED",
            user,
            entity_type="PROMPT",
            entity_ref=prompt.prompt_id,
            entity_name=prompt.name,
            details={"version": prompt.version, "changes": summary},
        )
    else:
        audit_service.record(
            db,
            "PROMPT_EDITED",
            user,
            entity_type="PROMPT",
            entity_ref=prompt.prompt_id,
            entity_name=prompt.name,
            details={"changes": changes[:10]},
        )
    db.commit()
    db.refresh(prompt)
    return prompt


def _version_label(n: int) -> str:
    if n == 1:
        return "1.0"
    if n == 2:
        return "1.1"
    return f"1.{n - 1}"


def _snapshot(prompt: Prompt) -> dict[str, Any]:
    return {
        "name": prompt.name,
        "description": prompt.description,
        "goal": prompt.goal,
        "context": prompt.context,
        "source": prompt.source,
        "expectations": prompt.expectations,
        "prompt_template": prompt.prompt_template,
        "business_function": prompt.business_function,
        "application": prompt.application,
        "task": prompt.task,
        "quality_score": prompt.quality_score,
    }


def clone_prompt(db: Session, prompt: Prompt, user: User, name: str | None = None) -> Prompt:
    new = Prompt(
        prompt_id=next_prompt_id(db),
        name=name or f"{prompt.name} (Copy)",
        description=prompt.description,
        status="DRAFT",
        version="1.0",
        version_number=1,
        owner_id=user.id,
        business_function=prompt.business_function,
        application=prompt.application,
        task=prompt.task,
        goal=prompt.goal,
        context=prompt.context,
        source=prompt.source,
        expectations=prompt.expectations,
        system_instruction=prompt.system_instruction,
        prompt_template=prompt.prompt_template,
        audience=prompt.audience,
        tone=prompt.tone,
        output_format=prompt.output_format,
        max_length=prompt.max_length,
        data_classification=prompt.data_classification,
        risk_level=prompt.risk_level,
        requires_approval=prompt.requires_approval,
        contains_pii=prompt.contains_pii,
        contains_financial_data=prompt.contains_financial_data,
        contains_customer_data=prompt.contains_customer_data,
        external_sharing=prompt.external_sharing,
        temperature=prompt.temperature,
        require_evidence=prompt.require_evidence,
        avoid_unsupported_claims=prompt.avoid_unsupported_claims,
        ask_clarification_questions=prompt.ask_clarification_questions,
        manual_time_minutes=prompt.manual_time_minutes,
        ai_time_minutes=prompt.ai_time_minutes,
        tags=list(prompt.tags or []),
        quality_score=prompt.quality_score,
    )
    db.add(new)
    db.flush()
    for item in prompt.inputs or []:
        new.inputs.append(
            PromptInput(
                prompt_id=new.id,
                name=item.name,
                input_type=item.input_type,
                required=item.required,
                description=item.description,
                sample_value=item.sample_value,
                position=item.position,
            )
        )
    new.versions.append(
        PromptVersion(
            prompt_id=new.id,
            version="1.0",
            version_number=1,
            author_id=user.id,
            changes="Cloned from " + prompt.prompt_id,
            snapshot=_snapshot(new),
        )
    )
    audit_service.record(
        db,
        "PROMPT_CLONED",
        user,
        entity_type="PROMPT",
        entity_ref=new.prompt_id,
        entity_name=new.name,
        details={"source": prompt.prompt_id},
    )
    db.commit()
    db.refresh(new)
    return new


def rate_prompt(db: Session, prompt: Prompt, user: User, data: RatingCreate) -> PromptRating:
    rating = db.scalar(
        select(PromptRating).where(
            PromptRating.prompt_id == prompt.id, PromptRating.user_id == user.id
        )
    )
    if rating is None:
        rating = PromptRating(prompt_id=prompt.id, user_id=user.id)
        db.add(rating)
    rating.stars = max(0, min(5, data.stars))
    rating.useful = data.useful
    rating.feedback = data.feedback
    audit_service.record(
        db,
        "PROMPT_RATED",
        user,
        entity_type="PROMPT",
        entity_ref=prompt.prompt_id,
        entity_name=prompt.name,
        details={"stars": data.stars, "useful": data.useful},
    )
    db.commit()
    return rating


def toggle_favourite(db: Session, prompt: Prompt, user: User) -> bool:
    fav = db.scalar(
        select(PromptFavourite).where(
            PromptFavourite.prompt_id == prompt.id, PromptFavourite.user_id == user.id
        )
    )
    if fav is not None:
        db.delete(fav)
        db.commit()
        return False
    db.add(PromptFavourite(prompt_id=prompt.id, user_id=user.id))
    audit_service.record(
        db,
        "PROMPT_FAVOURITED",
        user,
        entity_type="PROMPT",
        entity_ref=prompt.prompt_id,
        entity_name=prompt.name,
    )
    db.commit()
    return True


def popular_prompts(db: Session, limit: int = 6) -> list[Prompt]:
    return (
        db.query(Prompt)
        .outerjoin(PromptExecution)
        .group_by(Prompt.id)
        .order_by(func.count(PromptExecution.id).desc())
        .limit(limit)
        .all()
    )


def list_versions(db: Session, prompt: Prompt) -> list[PromptVersion]:
    return (
        db.query(PromptVersion)
        .where(PromptVersion.prompt_id == prompt.id)
        .order_by(PromptVersion.version_number.desc())
        .all()
    )


def get_version(db: Session, prompt: Prompt, version_ref: str) -> PromptVersion | None:
    return db.scalar(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt.id,
            or_(
                PromptVersion.version == version_ref,
                PromptVersion.version_number == _num(version_ref),
            ),
        )
    )


def compare_versions(old: PromptVersion, new: PromptVersion) -> list[str]:
    if not old or not new:
        return []
    o, n = old.snapshot or {}, new.snapshot or {}
    changes: list[str] = []
    for key in set(o) | set(n):
        if o.get(key) != n.get(key):
            changes.append(f"{key}: {o.get(key, '—')} → {n.get(key, '—')}")
    return changes


def _num(ref: str) -> int:
    try:
        return int(ref)
    except ValueError:
        return -1


def seed_fake_stats(db: Session, prompt: Prompt, executions: int, rating: float) -> None:
    """Deterministically add synthetic execution/rating rows for the demo."""
    for i in range(executions):
        db.add(
            PromptExecution(
                execution_id=f"EXEC-SEED-{prompt.prompt_id}-{i}",
                prompt_id=prompt.id,
                version=prompt.version,
                status="SUCCESS",
                provider="mock",
                model="MockAssistant",
                output="Synthetic execution for demo seeding.",
                tokens=120,
                latency_ms=340,
                execution_mode="SEED",
            )
        )
    db.add(
        PromptRating(
            prompt_id=prompt.id,
            user_id=prompt.owner_id,
            stars=rating,
            useful="YES",
        )
    )
    db.flush()


def ensure_demo_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.username == "henry"))
    if user:
        return user
    user = User(
        user_id=next_user_id(db),
        username="henry",
        display_name="Henry",
        email="henry@contoso.local",
        department="Data & Analytics",
        title="Enterprise Data Architect",
        role="GOVERNANCE",
    )
    db.add(user)
    db.flush()
    return user

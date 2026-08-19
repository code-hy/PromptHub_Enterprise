"""Demo seed — the whole enterprise dataset in one deterministic pass.

Resets and rebuilds the database so the demo is reproducible every boot.
Project Atlas story plus Contoso M365 data for RAG grounding.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import SessionLocal, init_db
from ..ids import (
    next_document_id,
    next_execution_id,
    next_policy_id,
    next_user_id,
    next_workflow_id,
)
from ..models import (
    Document,
    DocumentChunk,
    GovernancePolicy,
    KnowledgeSource,
    Prompt,
    PromptExecution,
    PromptInput,
    PromptRating,
    PromptVersion,
    SQLiteSequence,
    User,
    Workflow,
    WorkflowStep,
)
from ..quality.engine import analyse_prompt_fields
from ..security import hash_password
from .governance_catalog import POLICIES
from .prompts_catalog import PROMPTS
from .synthetic_m365 import build_all
from .users_catalog import USERS
from .workflows_catalog import WORKFLOWS

logger = logging.getLogger("prompthub.seed")

STATUS_WHEEL = [
    "PUBLISHED",
    "PUBLISHED",
    "PUBLISHED",
    "PUBLISHED",
    "PUBLISHED",
    "PUBLISHED",
    "PUBLISHED",
    "PUBLISHED",
    "PUBLISHED",
    "PUBLISHED",
    "PUBLISHED",
    "APPROVED",
    "APPROVED",
    "UNDER_REVIEW",
    "DRAFT",
    "DRAFT",
    "DEPRECATED",
]


def seed_all() -> None:
    init_db()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == "henry")):
            logger.info("Seed already present, skipping")
            return
        _seed_users(db)
        prompts = _seed_prompts(db)
        _seed_policies(db)
        docs = _seed_documents(db)
        _seed_knowledge_sources(db, prompts, docs)
        _seed_workflows(db, prompts)
        _seed_analytics_rows(db, prompts)
        db.commit()
        logger.info(
            "Seeded %d users, %d prompts, %d policies, %d documents, %d workflows",
            len(USERS),
            len(prompts),
            len(POLICIES),
            len(docs),
            len(WORKFLOWS),
        )


def _seed_users(db: Session) -> None:
    for data in USERS:
        db.add(
            User(
                user_id=next_user_id(db),
                username=data["username"],
                display_name=data["display_name"],
                email=data["email"],
                department=data["department"],
                title=data["title"],
                role=data["role"],
                password_hash=hash_password("password"),
            )
        )
    db.flush()


def _seed_prompts(db: Session) -> list[Prompt]:
    users = db.scalars(select(User).order_by(User.id)).all()
    prompts: list[Prompt] = []
    for idx, data in enumerate(PROMPTS):
        status = STATUS_WHEEL[idx % len(STATUS_WHEEL)]
        owner = users[idx % len(users)]
        prompt = Prompt(
            prompt_id=f"PROMPT-{idx + 1:06d}",
            name=data["name"],
            description=data.get("description", ""),
            status=status,
            version="1.0",
            version_number=1,
            owner_id=owner.id,
            business_function=data["business_function"],
            application=data["application"],
            task=data["task"],
            goal=data["goal"],
            context=data.get("context", ""),
            source=data.get("source", ""),
            expectations=data.get("expectations", ""),
            system_instruction=data.get("system_instruction", ""),
            prompt_template=data["template"],
            audience=data.get("audience", "GENERAL"),
            tone=data.get("tone", "PROFESSIONAL"),
            output_format=data.get("output_format", "FREE_TEXT"),
            max_length=data.get("max_length", ""),
            data_classification=data.get("data_classification", "INTERNAL"),
            risk_level=data.get("risk_level", "LOW"),
            requires_approval=data.get("risk_level") in ("HIGH", "CRITICAL")
            or data.get("data_classification") == "RESTRICTED",
            contains_pii=data.get("contains_pii", False),
            contains_financial_data=data.get("contains_financial_data", False),
            contains_customer_data=data.get("contains_customer_data", False),
            external_sharing=data.get("external_sharing", "PROHIBITED"),
            temperature=data.get("temperature", 0.2),
            require_evidence=data.get("require_evidence", False),
            avoid_unsupported_claims=data.get("avoid_unsupported_claims", False),
            ask_clarification_questions=data.get("ask_clarification_questions", False),
            manual_time_minutes=data.get("manual_time_minutes", 30.0),
            ai_time_minutes=data.get("ai_time_minutes", 5.0),
            tags=data.get("tags", []),
            quality_score=0,
            is_system=data.get("is_system", False),
            published_at=datetime.now(UTC) if status == "PUBLISHED" else None,
        )
        db.add(prompt)
        db.flush()
        analysis = analyse_prompt_fields(
            goal=prompt.goal,
            context=prompt.context,
            source=prompt.source,
            expectations=prompt.expectations,
            audience=prompt.audience,
            output_format=prompt.output_format,
        )
        prompt.quality_score = analysis.score
        db.flush()
        for input_data in data.get("inputs", []):
            db.add(
                PromptInput(
                    prompt_id=prompt.id,
                    name=input_data["name"],
                    input_type=input_data.get("type", "TEXT"),
                    required=input_data.get("required", True),
                    description=input_data.get("description", ""),
                    position=input_data.get("position", 0),
                )
            )
        version_snapshot = {
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
            "quality_score": analysis.score,
        }
        db.add(
            PromptVersion(
                prompt_id=prompt.id,
                version="1.0",
                author_id=owner.id,
                changes="Initial version",
                snapshot=version_snapshot,
            )
        )
        prompts.append(prompt)
    db.flush()

    # Advance the prompt counter so runtime creates never collide with seeded ids
    seq = db.scalar(select(SQLiteSequence).where(SQLiteSequence.counter_type == "prompt"))
    if seq is not None:
        seq.next_value = max(seq.next_value, len(PROMPTS) + 1)
    else:
        db.add(SQLiteSequence(counter_type="prompt", next_value=len(PROMPTS) + 1))
    db.flush()
    return prompts


def _seed_policies(db: Session) -> None:
    for data in POLICIES:
        db.add(
            GovernancePolicy(
                policy_id=next_policy_id(db),
                name=data["name"],
                description=data["description"],
                condition=data["condition"],
                action=data["action"],
                severity=data["severity"],
                enabled=True,
            )
        )
    db.flush()


def _seed_documents(db: Session) -> list[Document]:
    docs: list[Document] = []
    for data in build_all():
        doc = Document(
            doc_id=next_document_id(db),
            name=data["name"],
            doc_type=data["doc_type"],
            source_app=data["source_app"],
            department=data["department"],
            author=data["author"],
            summary=data["summary"],
            content=data["content"],
            metadata_=data["metadata_"],
            synthetic=True,
        )
        db.add(doc)
        db.flush()
        content = data["content"]
        step = 400
        for i in range(0, len(content), step):
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    chunk_index=i // step,
                    content=content[i : i + step],
                    char_start=i,
                    char_end=min(i + step, len(content)),
                )
            )
        docs.append(doc)
    db.flush()
    return docs


def _seed_knowledge_sources(db: Session, prompts: list[Prompt], docs: list[Document]) -> None:
    link_prompt_names = {
        "Project Risk Assessment",
        "Executive Summary",
        "Project Status",
        "Dataset Summary",
    }
    for prompt in prompts:
        if prompt.name not in link_prompt_names:
            continue
        for doc in docs:
            if (
                doc.department in (prompt.business_function, "PROJECT_MANAGEMENT")
                and prompt.name == "Project Risk Assessment"
            ):
                db.add(
                    KnowledgeSource(prompt_id=prompt.id, document_id=doc.id, source_type="DOCUMENT")
                )
            if prompt.name == "Executive Summary" and doc.name.lower().startswith("contoso"):
                db.add(
                    KnowledgeSource(prompt_id=prompt.id, document_id=doc.id, source_type="DOCUMENT")
                )
    db.flush()


def _seed_workflows(db: Session, prompts: list[Prompt]) -> None:
    prompt_by_name = {p.name: p for p in prompts}
    user = db.scalar(select(User).where(User.username == "sarah.chen")) or db.scalar(select(User))
    for data in WORKFLOWS:
        wf = Workflow(
            workflow_id=next_workflow_id(db),
            name=data["name"],
            description=data["description"],
            status="PUBLISHED",
            owner_id=user.id,
            business_function=data["business_function"],
            tags=data.get("tags", []),
            estimated_manual_minutes=data.get("estimated_manual_minutes", 45),
            estimated_ai_minutes=data.get("estimated_ai_minutes", 5),
        )
        db.add(wf)
        db.flush()
        for idx, step in enumerate(data["steps"], start=1):
            prompt = prompt_by_name.get(step["prompt_name"])
            if prompt is None:
                logger.warning(
                    "Workflow %s references missing prompt %s", data["name"], step["prompt_name"]
                )
                continue
            db.add(
                WorkflowStep(
                    workflow_id=wf.id,
                    step_id=f"STEP-{idx:03d}",
                    sequence=idx,
                    name=step["name"],
                    prompt_id=prompt.id,
                    input_mapping=step.get("mapping", {}),
                    continue_on_failure=step.get("continue_on_failure", False),
                )
            )
    db.flush()


def _seed_analytics_rows(db: Session, prompts: list[Prompt]) -> None:
    """Give the popular prompts believable synthetic execution/rating history."""
    popularity = {
        "Executive Summary": (620, 4.8),
        "Email Action Extractor": (540, 4.7),
        "Meeting Summary": (480, 4.6),
        "Email Priority Classifier": (420, 4.5),
        "Data Quality Assessment": (360, 4.7),
        "KPI Analysis": (300, 4.6),
        "Project Risk Assessment": (260, 4.8),
        "Executive Email Writer": (240, 4.5),
    }
    user = db.scalar(select(User).where(User.username == "henry"))
    for prompt in prompts:
        executions, rating = popularity.get(prompt.name, (0, 0.0))
        if executions <= 0:
            continue

        for i in range(min(executions, 40)):
            db.add(
                PromptExecution(
                    execution_id=next_execution_id(db),
                    prompt_id=prompt.id,
                    version=prompt.version,
                    user_id=user.id,
                    provider="mock",
                    model="MockAssistant",
                    temperature=prompt.temperature,
                    input_data={},
                    output="Synthetic execution for demo analytics.",
                    status="SUCCESS",
                    tokens=420,
                    latency_ms=340,
                    execution_mode="DEMO",
                )
            )
        if rating:
            db.add(
                PromptRating(
                    prompt_id=prompt.id,
                    user_id=user.id,
                    stars=rating,
                    useful="YES",
                )
            )
    db.flush()

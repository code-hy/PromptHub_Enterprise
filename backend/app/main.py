"""PromptHub Enterprise — FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db

logger = logging.getLogger("prompthub")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.seed_demo_data:
        try:
            from .seed import seed_all

            seed_all()
            logger.info("Demo seed complete")
        except Exception as exc:  # pragma: no cover - seeding should not block
            logger.exception("Seed failed: %s", exc)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Stand-Alone Enterprise AI Prompt Library, Engineering, Testing & Governance Platform",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from .api import (
        admin,
        analytics,
        assistant,
        audit,
        auth,
        catalog,
        executions,
        governance,
        knowledge,
        prompts,
        workflows,
    )

    for router in (
        catalog.router,
        auth.router,
        prompts.router,
        assistant.router,
        executions.router,
        workflows.router,
        governance.router,
        analytics.router,
        audit.router,
        admin.router,
        knowledge.router,
    ):
        app.include_router(router, prefix=settings.api_prefix)

    @app.get("/health", tags=["system"])
    def health():
        return {"status": "ok", "app": settings.app_name, "provider": settings.llm_provider}

    return app


app = create_app()

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
    # Always log to stdout so Render logs show it (logger alone may be filtered)
    print(f"[startup] seed_demo_data={settings.seed_demo_data} db={settings.sqlalchemy_url[:60]}...", flush=True)
    init_db()
    # Force seed when DB is empty — handles free-tier first boot and partial-seed recovery
    # even if SEED_DEMO_DATA was mis-set. Otherwise respect the flag.
    try:
        from sqlalchemy import func, select

        from .database import SessionLocal
        from .models import Prompt

        with SessionLocal() as _db:
            prompt_count = _db.scalar(select(func.count()).select_from(Prompt)) or 0
            print(f"[startup] prompt_count={prompt_count}", flush=True)
            should_seed = prompt_count == 0 or settings.seed_demo_data
            if should_seed and prompt_count == 0:
                print("[startup] DB empty — seeding demo data (68 prompts)...", flush=True)
                from .seed import seed_all

                seed_all()
                # re-count after seed
                with SessionLocal() as _db2:
                    c2 = _db2.scalar(select(func.count()).select_from(Prompt)) or 0
                    print(f"[startup] seed complete — now {c2} prompts", flush=True)
                    logger.info("Demo seed complete (%d prompts)", c2)
            elif settings.seed_demo_data:
                from .seed import seed_all

                seed_all()
                print("[startup] seed_demo_data seed complete", flush=True)
                logger.info("Demo seed complete")
            else:
                print("[startup] seed skipped (already has data and flag off)", flush=True)
    except Exception as exc:  # pragma: no cover - seeding should not block boot
        print(f"[startup] seed failed: {exc}", flush=True)
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

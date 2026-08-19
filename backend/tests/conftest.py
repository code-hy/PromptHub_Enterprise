"""Shared pytest fixtures — in-memory app + seeded database."""

from __future__ import annotations

import os
import tempfile

_tmp_db = os.path.join(tempfile.mkdtemp(), "test.db")

os.environ["LLM_PROVIDER"] = "mock"
os.environ["MOCK_LLM_LATENCY_MS"] = "0"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SEED_DEMO_DATA"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.main import create_app
from app.seed import seed_all


@pytest.fixture(scope="session")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def db():
    SessionLocal.remove()
    init_db()
    with SessionLocal() as session:
        seed_all()
        yield session

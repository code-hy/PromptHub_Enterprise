"""Database engine, session and declarative base.

Single source of truth for the SQLAlchemy wiring. `DATABASE_URL` decides
between SQLite (zero-dependency local demo) and PostgreSQL (production /
docker-compose).
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs() -> dict:
    url = settings.sqlalchemy_url
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


engine = create_engine(settings.sqlalchemy_url, **_engine_kwargs())


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _record):
    if settings.sqlalchemy_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Importing models registers them on the metadata."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    """Drop all tables (used by tests and `make reset`)."""
    from . import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)

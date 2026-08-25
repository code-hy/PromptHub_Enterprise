"""Application configuration loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PromptHub Enterprise"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # Defaults to a local SQLite file so the whole platform runs with zero
    # external infrastructure. Set DATABASE_URL to PostgreSQL in production.
    database_url: str = ""

    # LLM provider: auto | mock | ollama | openai | litellm
    llm_provider: str = "auto"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""
    litellm_base_url: str = "http://localhost:4000"
    litellm_model: str = ""

    rag_mode: str = "local"  # local | qdrant
    qdrant_url: str = "http://localhost:6333"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rag_enabled: bool = False

    secret_key: str = "change-me-to-a-long-random-string"
    access_token_expire_minutes: int = 720
    enable_auth: bool = False

    cors_origins: str = "http://localhost:5173,http://localhost:4173,http://127.0.0.1:5173,http://127.0.0.1:4173"

    mock_llm_latency_ms: int = 250
    llm_timeout_seconds: int = 300

    seed_demo_data: bool = True
    synthetic_m365_scale: str = "small"  # small | medium | large
    data_dir: str = str(BASE_DIR / "data")

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            url = self.database_url.strip()
            # Render and many PaaS still emit `postgres://` or `postgresql://`
            # which SQLAlchemy maps to psycopg2, but this project depends on
            # `psycopg[binary]` (psycopg 3, dialect `postgresql+psycopg`).
            # Normalize so both schemes work on Render free-tier.
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql+psycopg2://"):
                url = url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
            return url
        return f"sqlite:///{BASE_DIR / 'prompthub.db'}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def resolved_ollama_model(self) -> str:
        return self.ollama_model or "qwen3:1.7b"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

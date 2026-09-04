"""Application configuration (ADR-0002: config-driven).

Settings are read from the environment / a local `.env`. `get_settings()` is the
single accessor; tests construct `Settings(...)` directly and pass it to
`create_app()` rather than mutating global state.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Storage (ADR-0001: single Postgres + pgvector).
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/maverick"

    # Retrieval / answer policy (consumed from T3 onward; declared here so the
    # thresholds are configuration, never hard-coded — see the M1 spec).
    retrieval_top_k: int = 5
    grounding_threshold: float = 0.35

    # Ingestion / chunking (T2).
    chunk_max_chars: int = 1200
    chunk_overlap: int = 150

    # Model gateway roles (ADR-0002).
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    synthesis_model: str = "gpt-4o-mini"


@lru_cache
def get_settings() -> Settings:
    return Settings()

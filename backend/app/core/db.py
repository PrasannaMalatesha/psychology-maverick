"""Database access (ADR-0001: single Postgres + pgvector).

Small surface: build an engine, ensure the pgvector extension, and report health.
The engine is created from Settings and handed to the app; callers/tests never
reach for a global connection.
"""

from sqlalchemy import Engine, create_engine, text


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def ensure_pgvector(engine: Engine) -> None:
    """Create the `vector` extension if absent. Idempotent; proves pgvector is present."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


def check_health(engine: Engine) -> bool:
    """True when the database is reachable and the pgvector extension is installed."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            installed = conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).scalar()
        return installed == 1
    except Exception:
        return False

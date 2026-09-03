"""Test harness — the seams the whole spec relies on.

- A real ephemeral Postgres + pgvector database (testcontainers), never a fake store.
- The app exercised over HTTP via Starlette's TestClient.
- The model gateway is the one substituted dependency (FakeGateway) — see per-feature tests.
"""

import os

# Ryuk (testcontainers' reaper) mounts the docker socket, which Docker Desktop on
# macOS refuses. Disable it; the `with` context manager stops the container itself.
os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, text  # noqa: E402
from testcontainers.postgres import PostgresContainer  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.db import ensure_pgvector, make_engine  # noqa: E402
from app.core.llm import FakeGateway  # noqa: E402
from app.core.store import init_store  # noqa: E402
from app.features.corpus.service import CorpusService  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def pg():
    with PostgresContainer("pgvector/pgvector:pg16", driver="psycopg") as container:
        yield container


@pytest.fixture(scope="session")
def settings(pg) -> Settings:
    return Settings(database_url=pg.get_connection_url())


@pytest.fixture(scope="session")
def client(settings):
    app = create_app(settings)
    with TestClient(app) as c:  # context-manager runs lifespan -> ensure_pgvector + init_store
        yield c


@pytest.fixture(scope="session")
def engine(settings) -> Engine:
    eng = make_engine(settings.database_url)
    ensure_pgvector(eng)
    init_store(eng)
    return eng


@pytest.fixture
def clean_passages(engine: Engine):
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE passages"))
    yield


@pytest.fixture
def corpus_service(engine: Engine, settings: Settings) -> CorpusService:
    return CorpusService(engine, FakeGateway(), settings)

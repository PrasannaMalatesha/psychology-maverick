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
from testcontainers.postgres import PostgresContainer  # noqa: E402

from app.core.config import Settings
from app.main import create_app


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
    with TestClient(app) as c:  # context-manager runs lifespan -> ensure_pgvector
        yield c

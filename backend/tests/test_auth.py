"""M6 auth & security: register/login, JWT protection, refresh rotation, RBAC, per-User ownership.

Exercised over the HTTP seam against real Postgres; the model gateway is FakeGateway. Each helper
builds its own app so token/ownership state is isolated per test.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.llm import FakeGateway
from app.main import create_app

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"


@pytest.fixture
def app_client(settings: Settings):
    with TestClient(create_app(settings, gateway=FakeGateway())) as c:
        yield c


def _register_and_login(client: TestClient, email: str, password: str = "password123") -> str:
    client.post("/auth/register", json={"email": email, "password": password})
    tokens = client.post("/auth/login", json={"email": email, "password": password}).json()
    return tokens["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- register / login -----------------------------------------------------------------------


def test_register_then_login_issues_tokens(app_client: TestClient):
    r = app_client.post("/auth/register", json={"email": "a@test.local", "password": "password123"})
    assert r.status_code == 201
    assert r.json()["role"] == "user"

    r = app_client.post("/auth/login", json={"email": "a@test.local", "password": "password123"})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["refresh_token"]


def test_duplicate_email_is_rejected(app_client: TestClient):
    body = {"email": "dup@test.local", "password": "password123"}
    app_client.post("/auth/register", json=body)
    assert app_client.post("/auth/register", json=body).status_code == 409


def test_wrong_password_is_unauthorized(app_client: TestClient):
    app_client.post("/auth/register", json={"email": "b@test.local", "password": "password123"})
    r = app_client.post("/auth/login", json={"email": "b@test.local", "password": "WRONG-pass"})
    assert r.status_code == 401


# --- token protection -----------------------------------------------------------------------


def test_chat_requires_authentication(app_client: TestClient):
    r = app_client.post("/chat", json={"query": "what is cognitive behavioral therapy?"})
    assert r.status_code == 401


def test_garbage_token_is_rejected(app_client: TestClient):
    r = app_client.post("/chat", json={"query": "x"}, headers=_auth("not-a-real-jwt"))
    assert r.status_code == 401


def test_health_stays_public(app_client: TestClient):
    assert app_client.get("/health").status_code in (200, 503)


# --- refresh rotation / logout --------------------------------------------------------------


def test_refresh_rotates_and_old_token_is_revoked(app_client: TestClient):
    app_client.post("/auth/register", json={"email": "r@test.local", "password": "password123"})
    tokens = app_client.post(
        "/auth/login", json={"email": "r@test.local", "password": "password123"}
    ).json()

    rotated = app_client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != tokens["refresh_token"]

    # The original refresh token was revoked on rotation — reuse is rejected.
    reused = app_client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reused.status_code == 401


def test_logout_revokes_refresh_token(app_client: TestClient):
    app_client.post("/auth/register", json={"email": "o@test.local", "password": "password123"})
    tokens = app_client.post(
        "/auth/login", json={"email": "o@test.local", "password": "password123"}
    ).json()

    logout = app_client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout.status_code == 204
    after = app_client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert after.status_code == 401


# --- RBAC -----------------------------------------------------------------------------------


def test_admin_route_forbidden_for_regular_user(app_client: TestClient):
    token = _register_and_login(app_client, "plainuser@test.local")
    assert app_client.get("/admin/corpus-stats", headers=_auth(token)).status_code == 403


def test_admin_route_allowed_for_admin(settings: Settings):
    # Seed an admin directly through the service (registration only ever mints `user`).
    app = create_app(settings, gateway=FakeGateway())
    with TestClient(app) as c:  # lifespan creates the tables first
        app.state.auth_service.register("boss@test.local", "password123", role="admin")
        tokens = c.post(
            "/auth/login", json={"email": "boss@test.local", "password": "password123"}
        ).json()
        r = c.get("/admin/corpus-stats", headers=_auth(tokens["access_token"]))
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# --- per-User conversation ownership (IDOR) -------------------------------------------------


def test_user_cannot_read_another_users_conversation(
    clean_passages, corpus_service, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    with TestClient(create_app(settings, gateway=FakeGateway())) as c:
        alice = _register_and_login(c, "alice@test.local")
        bob = _register_and_login(c, "bob@test.local")

        cid = c.post(
            "/chat", json={"query": "what is cognitive behavioral therapy?"}, headers=_auth(alice)
        ).headers["X-Conversation-Id"]

        # Alice can read her own conversation…
        assert c.get(f"/conversations/{cid}", headers=_auth(alice)).status_code == 200
        # …Bob cannot (403, IDOR defense).
        assert c.get(f"/conversations/{cid}", headers=_auth(bob)).status_code == 403
        # …and Bob cannot post into it either.
        posted = c.post("/chat", json={"query": "x", "conversation_id": cid}, headers=_auth(bob))
        assert posted.status_code == 403


def test_email_is_case_insensitive(app_client: TestClient):
    app_client.post("/auth/register", json={"email": "Case@Test.local", "password": "password123"})
    dup = app_client.post(
        "/auth/register", json={"email": "case@test.local", "password": "password123"}
    )
    assert dup.status_code == 409
    login = app_client.post(
        "/auth/login", json={"email": "CASE@test.local", "password": "password123"}
    )
    assert login.status_code == 200

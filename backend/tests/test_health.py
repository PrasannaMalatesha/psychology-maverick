"""Behavior of GET /health and the /chat seam, across the HTTP interface."""

from app.core.db import check_health, make_engine


def test_health_ok_when_db_reachable(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}


def test_health_reports_degraded_when_db_unreachable():
    # No container: an engine pointed at a dead address must report unhealthy,
    # not raise. Exercises check_health's failure path directly.
    engine = make_engine("postgresql+psycopg://x:x@127.0.0.1:1/none")
    assert check_health(engine) is False

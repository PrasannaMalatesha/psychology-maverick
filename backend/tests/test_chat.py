"""Grounded /chat behavior across the HTTP seam (seeded fixtures, FakeGateway)."""

from pathlib import Path

from sqlalchemy import Engine, text

from app.features.corpus.service import CorpusService

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"


def test_chat_returns_grounded_cited_answer(
    clean_passages, corpus_service: CorpusService, client, engine: Engine
):
    corpus_service.ingest(str(FIXTURES))
    r = client.post("/chat", json={"query": "What is cognitive behavioral therapy?"})
    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "grounded"
    assert body["text"]
    assert len(body["citations"]) >= 1
    # Citation serializes with the glossary term "register" (wire alias).
    assert "register" in body["citations"][0]


def test_citations_resolve_to_real_passages(
    clean_passages, corpus_service: CorpusService, client, engine: Engine
):
    corpus_service.ingest(str(FIXTURES))
    body = client.post("/chat", json={"query": "how does sleep affect mood?"}).json()
    cited = {c["passage_id"] for c in body["citations"]}
    with engine.connect() as conn:
        existing = {row[0] for row in conn.execute(text("SELECT passage_id FROM passages"))}
    assert cited and cited <= existing  # every cited passage is a real, stored passage

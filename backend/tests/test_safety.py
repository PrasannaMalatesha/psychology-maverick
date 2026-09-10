"""M4 safety controls (ADR-0004): crisis routing, faithfulness judge, HITL, disclaimer.

Exercised through the service and HTTP seams over real pgvector; the model gateway is the
one stub. The fixture corpus is clinical, so grounded answers here are clinical answers.
"""

from pathlib import Path

from sqlalchemy import Engine

from app.core.config import Settings
from app.core.llm import FakeGateway
from app.features.chat.service import ChatService
from app.features.corpus.service import CorpusService
from app.features.retrieval.service import RetrievalService

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"


def _chat(engine: Engine, settings: Settings, gateway: FakeGateway | None = None) -> ChatService:
    gw = gateway or FakeGateway()
    return ChatService(RetrievalService(engine, gw), gw, settings)


class _UnfaithfulGateway(FakeGateway):
    """A gateway whose faithfulness judge always rejects — forces the downgrade path."""

    def is_faithful(self, *, context: str, answer: str) -> bool:
        return False


# --- Crisis routing -----------------------------------------------------------------------

def test_crisis_query_surfaces_resources_and_stops(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    answer = _chat(engine, settings).answer("I want to kill myself", "crisis-1")
    assert answer.state.value == "crisis"
    assert "988" in (answer.text or "")
    assert not answer.citations  # no retrieval happened
    assert answer.category is None


def test_crisis_short_circuits_before_retrieval(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    # No corpus ingested: a normal query would be insufficient, but a crisis query still
    # returns resources — proving the crisis gate runs before (and instead of) retrieval.
    answer = _chat(engine, settings).answer("sometimes I think about ending my life", "crisis-2")
    assert answer.state.value == "crisis"


def test_non_crisis_query_is_unaffected(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    answer = _chat(engine, settings).answer("what is cognitive behavioral therapy?", "ok-1")
    assert answer.state.value == "grounded"


def test_crisis_detected_over_http(clean_passages, corpus_service: CorpusService, client):
    corpus_service.ingest(str(FIXTURES))
    r = client.post("/chat", json={"query": "I want to hurt myself"})
    assert r.status_code == 200
    assert r.json()["state"] == "crisis"


# --- Faithfulness judge -------------------------------------------------------------------

def test_unfaithful_answer_is_downgraded_to_insufficient(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    chat = _chat(engine, settings, gateway=_UnfaithfulGateway())
    # Semantic retrieval finds passages (threshold 0.0) so the answer would be grounded,
    # but the judge rejects it → insufficient_context, no fabricated answer served.
    answer = chat.answer("what is cognitive behavioral therapy?", "judge-1")
    assert answer.state.value == "insufficient_context"
    assert answer.text is None
    assert not answer.citations


# --- Clinical disclaimer ------------------------------------------------------------------

def test_grounded_clinical_answer_carries_disclaimer(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    answer = _chat(engine, settings).answer("what is cognitive behavioral therapy?", "disc-1")
    assert answer.state.value == "grounded"
    assert answer.category is not None and answer.category.value == "clinical"
    assert answer.disclaimer and "not medical advice" in answer.disclaimer


def test_crisis_answer_has_no_disclaimer(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    answer = _chat(engine, settings).answer("I want to die", "disc-2")
    assert answer.state.value == "crisis"
    assert answer.disclaimer is None


# --- Human-in-the-loop interrupt ----------------------------------------------------------

def _needs_review(settings: Settings) -> Settings:
    # Force every grounded clinical answer below the confidence bar → interrupt.
    return settings.model_copy(update={"clinical_confidence_threshold": 1.0})


def test_low_confidence_clinical_interrupts_then_approves(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    chat = _chat(engine, _needs_review(settings))

    held = chat.answer("what is cognitive behavioral therapy?", "hitl-1")
    assert held.state.value == "pending_review"  # paused for a human

    resolved = chat.review("hitl-1", "approve")
    assert resolved.state.value == "grounded"
    assert resolved.citations
    assert len(chat.history("hitl-1")) == 1  # only the served (approved) turn is recorded


def test_low_confidence_clinical_can_be_rejected(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    chat = _chat(engine, _needs_review(settings))

    held = chat.answer("what is cognitive behavioral therapy?", "hitl-2")
    assert held.state.value == "pending_review"

    withheld = chat.review("hitl-2", "reject")
    assert withheld.state.value == "pending_review"  # withheld, not served
    assert not withheld.citations


def test_review_resume_over_http(clean_passages, corpus_service: CorpusService, settings: Settings):
    corpus_service.ingest(str(FIXTURES))
    # A fresh app configured to route every clinical answer to review (in-process MemorySaver
    # persists the interrupt across the two requests).
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app(_needs_review(settings), gateway=FakeGateway())
    with TestClient(app) as c:
        first = c.post("/chat", json={"query": "what is cognitive behavioral therapy?"})
        assert first.json()["state"] == "pending_review"
        cid = first.headers["X-Conversation-Id"]

        resumed = c.post(f"/conversations/{cid}/review", json={"decision": "approve"})
        assert resumed.status_code == 200
        assert resumed.json()["state"] == "grounded"

"""Insufficient Context + no-fabrication (grounded-or-silent, ADR-0004).

The threshold branch is driven deterministically by the threshold value, not by
guessing the fake embeddings' magnitudes.
"""

from pathlib import Path

from sqlalchemy import Engine

from app.core.config import Settings
from app.core.llm import FakeGateway
from app.features.chat.service import ChatService
from app.features.corpus.service import CorpusService
from app.features.retrieval.service import RetrievalService

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"


def _chat(engine: Engine, gateway: FakeGateway, settings: Settings) -> ChatService:
    return ChatService(RetrievalService(engine, gateway), gateway, settings)


def test_insufficient_when_nothing_clears_threshold(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    strict = settings.model_copy(update={"grounding_threshold": 2.0})  # nothing can score >= 2.0
    answer = _chat(engine, FakeGateway(), strict).answer("cognitive behavioral therapy")
    assert answer.state.value == "insufficient_context"
    assert answer.text is None
    assert answer.category is None
    assert answer.citations == []


def test_insufficient_when_store_is_empty(
    clean_passages, engine: Engine, settings: Settings
):
    # No ingestion: retrieval returns nothing, so the answer must decline.
    answer = _chat(engine, FakeGateway(), settings).answer("cognitive behavioral therapy")
    assert answer.state.value == "insufficient_context"


class _SpyGateway(FakeGateway):
    def __init__(self) -> None:
        self.synth_calls = 0

    def synthesize(self, *, context: str, query: str) -> str:
        self.synth_calls += 1
        return super().synthesize(context=context, query=query)


def test_synthesis_not_invoked_when_insufficient(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    spy = _SpyGateway()
    strict = settings.model_copy(update={"grounding_threshold": 2.0})
    answer = _chat(engine, spy, strict).answer("cognitive behavioral therapy")
    assert answer.state.value == "insufficient_context"
    assert spy.synth_calls == 0


def test_citations_reference_only_retrieved_passages(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    gateway = FakeGateway()
    retrieval = RetrievalService(engine, gateway)
    chat = ChatService(retrieval, gateway, settings)
    query = "cognitive behavioral therapy"

    qualifying = {
        p.passage_id
        for p in retrieval.retrieve(query, settings.retrieval_top_k)
        if p.score >= settings.grounding_threshold
    }
    answer = chat.answer(query)

    cited = {c.passage_id for c in answer.citations}
    assert cited == qualifying  # exactly the retrieved, grounded passages — nothing invented

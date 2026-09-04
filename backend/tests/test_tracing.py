"""One trace per Query, with spans matching the phases actually run."""

from pathlib import Path

from sqlalchemy import Engine

from app.core.config import Settings
from app.core.llm import FakeGateway
from app.core.observability import RecordingTracer
from app.features.chat.service import ChatService
from app.features.corpus.service import CorpusService
from app.features.retrieval.service import RetrievalService

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"


def _chat(engine: Engine, settings: Settings, tracer: RecordingTracer) -> ChatService:
    gateway = FakeGateway()
    return ChatService(RetrievalService(engine, gateway), gateway, settings, tracer=tracer)


def test_grounded_query_emits_one_trace_with_retrieve_and_synthesize_spans(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    rec = RecordingTracer()
    _chat(engine, settings, rec).answer("cognitive behavioral therapy")
    assert len(rec.traces) == 1
    assert rec.traces[0]["spans"] == ["retrieve", "synthesize"]


def test_insufficient_query_emits_one_trace_without_synthesize_span(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    rec = RecordingTracer()
    strict = settings.model_copy(update={"grounding_threshold": 2.0})
    _chat(engine, strict, rec).answer("cognitive behavioral therapy")
    assert len(rec.traces) == 1
    assert rec.traces[0]["spans"] == ["retrieve"]

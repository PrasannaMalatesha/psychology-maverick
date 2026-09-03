"""Retrieval behavior: top-k limit and similarity ordering over real pgvector."""

from pathlib import Path

from sqlalchemy import Engine

from app.core.llm import FakeGateway
from app.features.corpus.service import CorpusService
from app.features.retrieval.service import RetrievalService

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"


def test_retrieve_respects_top_k_and_orders_by_similarity(
    clean_passages, corpus_service: CorpusService, engine: Engine
):
    corpus_service.ingest(str(FIXTURES))
    retrieval = RetrievalService(engine, FakeGateway())

    results = retrieval.retrieve("anxiety and persistent worry", k=3)

    assert 1 <= len(results) <= 3
    scores = [p.score for p in results]
    assert scores == sorted(scores, reverse=True)  # most-similar first
    assert all(0.0 <= s <= 1.0 for s in scores)

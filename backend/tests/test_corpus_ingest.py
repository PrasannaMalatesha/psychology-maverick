"""Ingestion behavior through the CLI seam, against real pgvector with a fake gateway."""

from pathlib import Path

from sqlalchemy import Engine, text

from app.core.config import Settings
from app.core.llm import FakeGateway
from app.core.llm.gateway import EMBEDDING_DIM
from app.features.corpus import cli
from app.features.corpus.service import CorpusService

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"


def _scalar(engine: Engine, sql: str) -> object:
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


def _distinct(engine: Engine, sql: str) -> set[object]:
    with engine.connect() as conn:
        return {row[0] for row in conn.execute(text(sql))}


def test_ingest_stores_passages_across_registers(
    clean_passages, corpus_service: CorpusService, engine: Engine
):
    report = cli.run(["ingest", str(FIXTURES)], service=corpus_service)
    assert report.documents == 3
    # The CBT overview exceeds the chunk cap, so passages outnumber documents.
    assert report.passages > 3
    assert _distinct(engine, "SELECT DISTINCT register FROM passages") == {
        "textbook",
        "research",
        "consumer_health",
    }


def test_register_inferred_from_parent_directory(
    clean_passages, corpus_service: CorpusService, engine: Engine
):
    cli.run(["ingest", str(FIXTURES)], service=corpus_service)
    # sleep.md has no front-matter register; it must be inferred from articles/ -> research.
    assert _distinct(
        engine, "SELECT register FROM passages WHERE source_ref LIKE '%sleep.md'"
    ) == {"research"}


def test_category_comes_from_front_matter(
    clean_passages, corpus_service: CorpusService, engine: Engine
):
    cli.run(["ingest", str(FIXTURES)], service=corpus_service)
    assert _distinct(
        engine, "SELECT DISTINCT category FROM passages WHERE source_ref LIKE '%cbt.md'"
    ) == {"clinical"}


def test_embeddings_stored_at_expected_dimension(
    clean_passages, corpus_service: CorpusService, engine: Engine
):
    cli.run(["ingest", str(FIXTURES)], service=corpus_service)
    assert _scalar(engine, "SELECT vector_dims(embedding) FROM passages LIMIT 1") == EMBEDDING_DIM


def test_reingest_is_idempotent(
    clean_passages, corpus_service: CorpusService, engine: Engine
):
    first = cli.run(["ingest", str(FIXTURES)], service=corpus_service)
    count_after_first = _scalar(engine, "SELECT count(*) FROM passages")
    second = cli.run(["ingest", str(FIXTURES)], service=corpus_service)
    count_after_second = _scalar(engine, "SELECT count(*) FROM passages")
    assert first.passages == second.passages
    assert count_after_first == count_after_second  # no duplicates on re-ingest


def test_reingest_shortened_document_leaves_no_orphans(
    clean_passages, engine: Engine, settings: Settings, tmp_path
):
    articles = tmp_path / "articles"
    articles.mkdir()
    doc = articles / "doc.md"
    front = "---\ntitle: Doc\nregister: research\ncategory: clinical\n---\n"
    service = CorpusService(engine, FakeGateway(), settings)

    doc.write_text(front + "# A\n" + ("word " * 800))  # long -> several chunks
    first = service.ingest(str(tmp_path))
    assert first.passages > 1

    doc.write_text(front + "# A\nshort body.")  # same source_ref, now one chunk
    second = service.ingest(str(tmp_path))

    assert second.passages == 1
    assert _scalar(engine, "SELECT count(*) FROM passages") == 1  # long version fully gone

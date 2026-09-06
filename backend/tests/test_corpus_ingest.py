"""Ingestion behavior through the CLI seam, against real pgvector with a fake gateway."""

import json
from pathlib import Path

from sqlalchemy import Engine, text

from app.core.config import Settings
from app.core.llm import FakeGateway
from app.core.llm.gateway import EMBEDDING_DIM
from app.core.store import corpus_stats
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
    report = corpus_service.ingest(str(FIXTURES))
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
    assert _distinct(engine, "SELECT register FROM passages WHERE source_ref LIKE '%sleep.md'") == {
        "research"
    }


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


def test_reingest_is_idempotent(clean_passages, corpus_service: CorpusService, engine: Engine):
    first = corpus_service.ingest(str(FIXTURES))
    count_after_first = _scalar(engine, "SELECT count(*) FROM passages")
    second = corpus_service.ingest(str(FIXTURES))
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


def test_every_passage_has_a_category(
    clean_passages, corpus_service: CorpusService, engine: Engine
):
    corpus_service.ingest(str(FIXTURES))
    assert _scalar(engine, "SELECT count(*) FROM passages WHERE category IS NULL") == 0


def test_json_manifest_titles_the_matching_article(
    clean_passages, engine: Engine, settings: Settings, tmp_path
):
    articles = tmp_path / "articles"
    articles.mkdir()
    (articles / "plos.json").write_text(
        json.dumps(
            {
                "response": {
                    "docs": [
                        {
                            "id": "10.1371/journal.pone.0197002",
                            "title_display": "Diurnal Variations",
                        }
                    ]
                }
            }
        )
    )
    # An article body file whose stem carries the DOI's trailing segment; no front-matter title.
    (articles / "plos_pone_0197002.txt").write_text("# Body\nresearch text on circadian mood.")
    CorpusService(engine, FakeGateway(), settings).ingest(str(tmp_path))

    titles = _distinct(engine, "SELECT DISTINCT document_title FROM passages")
    assert "Diurnal Variations" in titles  # manifest title used, not the filename stem
    assert _distinct(engine, "SELECT DISTINCT register FROM passages") == {"research"}


def test_corpus_stats_counts_per_register(
    clean_passages, corpus_service: CorpusService, engine: Engine
):
    corpus_service.ingest(str(FIXTURES))
    stats = {s.register: s for s in corpus_stats(engine)}
    assert set(stats) == {"textbook", "research", "consumer_health"}
    assert all(s.documents == 1 for s in stats.values())
    assert all(s.passages >= 1 for s in stats.values())


def test_cli_stats_reports_per_register(
    clean_passages, corpus_service: CorpusService, engine: Engine
):
    corpus_service.ingest(str(FIXTURES))
    stats = cli.run(["stats"], engine=engine)
    assert isinstance(stats, list)
    assert {s.register for s in stats} == {"textbook", "research", "consumer_health"}


def test_ingest_skips_unreadable_and_empty_sources(
    clean_passages, engine: Engine, settings: Settings, tmp_path
):
    articles = tmp_path / "articles"
    articles.mkdir()
    (articles / "good.md").write_text(
        "---\ntitle: Good\ncategory: clinical\n---\n# A\nreal content."
    )
    (articles / "empty.txt").write_text("")  # empty -> skipped
    (articles / "broken.pdf").write_text("this is not a pdf")  # unreadable -> skipped

    report = CorpusService(engine, FakeGateway(), settings).ingest(str(tmp_path))

    assert report.documents == 1
    assert report.skipped == 2
    assert report.passages >= 1

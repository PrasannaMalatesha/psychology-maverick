"""Thin CLI adapter over the `corpus` feature (ADR-0006).

    python -m app.features.corpus.cli ingest <path>
    python -m app.features.corpus.cli stats
"""

from __future__ import annotations

import argparse

from sqlalchemy import Engine

from app.core.config import Settings, get_settings
from app.core.db import ensure_pgvector, make_engine
from app.core.llm.production_gateway import ProductionGateway
from app.core.store import RegisterStats, corpus_stats, init_store
from app.features.corpus.service import CorpusService, IngestReport


def _prepare_engine(settings: Settings) -> Engine:
    engine = make_engine(settings.database_url)
    ensure_pgvector(engine)
    init_store(engine)
    return engine


def build_service(settings: Settings) -> CorpusService:
    return CorpusService(_prepare_engine(settings), ProductionGateway(settings), settings)


def run(
    argv: list[str],
    service: CorpusService | None = None,
    engine: Engine | None = None,
) -> IngestReport | list[RegisterStats]:
    parser = argparse.ArgumentParser(prog="corpus")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="Ingest a corpus subset from a directory")
    ingest.add_argument("path", help="Directory of source documents")
    sub.add_parser("stats", help="Show documents and passages per register")
    args = parser.parse_args(argv)

    settings = get_settings()
    if args.command == "ingest":
        service = service or build_service(settings)
        report = service.ingest(args.path)
        print(
            f"Ingested {report.documents} documents, {report.passages} passages "
            f"({report.skipped} skipped)"
        )
        return report

    stats = corpus_stats(engine or _prepare_engine(settings))
    for s in stats:
        print(f"{s.register}: {s.documents} documents, {s.passages} passages")
    return stats


def main() -> None:
    import sys

    run(sys.argv[1:])


if __name__ == "__main__":
    main()

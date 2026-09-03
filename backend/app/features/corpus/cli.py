"""Thin CLI adapter over `corpus.ingest` (ADR-0006).

Usage: `python -m app.features.corpus.cli ingest <path>`
"""

from __future__ import annotations

import argparse

from app.core.config import Settings, get_settings
from app.core.db import ensure_pgvector, make_engine
from app.core.llm.production_gateway import ProductionGateway
from app.core.store import init_store
from app.features.corpus.service import CorpusService, IngestReport


def build_service(settings: Settings) -> CorpusService:
    engine = make_engine(settings.database_url)
    ensure_pgvector(engine)
    init_store(engine)
    return CorpusService(engine, ProductionGateway(settings), settings)


def run(argv: list[str], service: CorpusService | None = None) -> IngestReport:
    parser = argparse.ArgumentParser(prog="corpus")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="Ingest a corpus subset from a directory")
    ingest.add_argument("path", help="Directory of source documents")
    args = parser.parse_args(argv)

    service = service or build_service(get_settings())
    report = service.ingest(args.path)
    print(f"Ingested {report.documents} documents, {report.passages} passages")
    return report


def main() -> None:
    import sys

    run(sys.argv[1:])


if __name__ == "__main__":
    main()

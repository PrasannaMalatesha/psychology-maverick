"""The `corpus` service — ingestion (write path) into the passage store (ADR-0006).

Small interface: `ingest(source) -> IngestReport`. Hides chunking, metadata,
batched embedding (via the gateway), and idempotent upsert. Driven by a thin CLI
adapter. Implemented in T2.
"""

from dataclasses import dataclass

from sqlalchemy import Engine

from app.core.llm.gateway import ModelGateway


@dataclass(frozen=True)
class IngestReport:
    documents: int
    passages: int


class CorpusService:
    def __init__(self, engine: Engine, gateway: ModelGateway) -> None:
        self._engine = engine
        self._gateway = gateway

    def ingest(self, source: str) -> IngestReport:
        raise NotImplementedError("corpus.ingest lands in T2")

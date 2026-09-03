"""The `corpus` service — ingestion (write path) into the passage store (ADR-0006).

Small interface: `ingest(path) -> IngestReport`. Hides document loading, structure-aware
chunking, batched embedding (via the gateway), and idempotent upsert. Accepts its
dependencies (engine, gateway, settings) rather than constructing them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine

from app.core.config import Settings
from app.core.llm.gateway import ModelGateway
from app.core.store import PassageRecord, upsert_passages
from app.features.corpus.chunking import chunk_document
from app.features.corpus.documents import load_documents

_EMBED_BATCH = 64


@dataclass(frozen=True)
class IngestReport:
    documents: int
    passages: int


class CorpusService:
    def __init__(self, engine: Engine, gateway: ModelGateway, settings: Settings) -> None:
        self._engine = engine
        self._gateway = gateway
        self._settings = settings

    def _embed_all(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _EMBED_BATCH):
            vectors.extend(self._gateway.embed(texts[start : start + _EMBED_BATCH]))
        return vectors

    def ingest(self, path: str) -> IngestReport:
        docs = load_documents(Path(path))
        pending = [
            (doc, chunk)
            for doc in docs
            for chunk in chunk_document(
                doc, self._settings.chunk_max_chars, self._settings.chunk_overlap
            )
        ]
        embeddings = self._embed_all([chunk.text for _, chunk in pending])
        records = [
            PassageRecord(
                passage_id=chunk.passage_id,
                document_title=doc.title,
                register=doc.register.value,
                category=doc.category.value if doc.category else None,
                locator=chunk.locator,
                text=chunk.text,
                source_ref=doc.source_ref,
                embedding=embedding,
            )
            for (doc, chunk), embedding in zip(pending, embeddings, strict=True)
        ]
        upsert_passages(self._engine, records)
        return IngestReport(documents=len(docs), passages=len(records))

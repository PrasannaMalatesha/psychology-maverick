"""The passage store — shared persistence for the corpus (ADR-0001).

`corpus` writes passages here (ingestion); `retrieval` reads them (T3). It lives in
core so neither feature imports the other. One concrete implementation over Postgres +
pgvector; tested through a real ephemeral database, never a fake (ADR-0006).
"""

from dataclasses import dataclass

from pgvector.sqlalchemy import Vector
from sqlalchemy import Engine, String, Text, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.core.llm.gateway import EMBEDDING_DIM


class Passage(Base):
    __tablename__ = "passages"

    passage_id: Mapped[str] = mapped_column(String, primary_key=True)
    document_title: Mapped[str] = mapped_column(String)
    register: Mapped[str] = mapped_column(String)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    locator: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str] = mapped_column(String)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))


@dataclass(frozen=True)
class PassageRecord:
    passage_id: str
    document_title: str
    register: str
    category: str | None
    locator: str
    text: str
    source_ref: str
    embedding: list[float]


def init_store(engine: Engine) -> None:
    """Create the passages table and its HNSW index. Idempotent."""
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_passages_embedding "
                "ON passages USING hnsw (embedding vector_cosine_ops)"
            )
        )


def upsert_passages(engine: Engine, records: list[PassageRecord]) -> int:
    """Insert or update passages by passage_id (idempotent re-ingest). Returns the count."""
    if not records:
        return 0
    rows = [
        {
            "passage_id": r.passage_id,
            "document_title": r.document_title,
            "register": r.register,
            "category": r.category,
            "locator": r.locator,
            "text": r.text,
            "source_ref": r.source_ref,
            "embedding": r.embedding,
        }
        for r in records
    ]
    stmt = pg_insert(Passage).values(rows)
    update_cols = {c: stmt.excluded[c] for c in rows[0] if c != "passage_id"}
    stmt = stmt.on_conflict_do_update(index_elements=["passage_id"], set_=update_cols)
    with engine.begin() as conn:
        conn.execute(stmt)
    return len(rows)

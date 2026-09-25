"""The passage store — shared persistence for the corpus (ADR-0001).

`corpus` writes passages here (ingestion); `retrieval` reads them (T3). It lives in
core so neither feature imports the other. One concrete implementation over Postgres +
pgvector; tested through a real ephemeral database, never a fake (ADR-0006).
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from pgvector.sqlalchemy import Vector
from sqlalchemy import Engine, Row, String, Text, delete, insert, select, text
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


class User(Base):
    """An authenticated person (ADR project.md §9). Password is argon2-hashed, never plaintext."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="user")


class ConversationOwner(Base):
    """Maps a conversation to the User who created it — per-user ownership (IDOR defense, §9)."""

    __tablename__ = "conversation_owners"

    conversation_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)


def create_user(engine: Engine, *, id: str, email: str, password_hash: str, role: str) -> None:
    """Insert a User. Raises on a duplicate email (unique constraint) — caller maps to 409."""
    with engine.begin() as conn:
        conn.execute(
            insert(User).values(id=id, email=email, password_hash=password_hash, role=role)
        )


def get_user_by_email(engine: Engine, email: str) -> Row | None:
    with engine.connect() as conn:
        return conn.execute(select(User).where(User.email == email)).first()


def get_user_by_id(engine: Engine, user_id: str) -> Row | None:
    with engine.connect() as conn:
        return conn.execute(select(User).where(User.id == user_id)).first()


def set_conversation_owner(engine: Engine, conversation_id: str, user_id: str) -> None:
    """Record the owner on first write; later writes for the same conversation are a no-op."""
    with engine.begin() as conn:
        conn.execute(
            pg_insert(ConversationOwner)
            .values(conversation_id=conversation_id, user_id=user_id)
            .on_conflict_do_nothing(index_elements=["conversation_id"])
        )


def get_conversation_owner(engine: Engine, conversation_id: str) -> str | None:
    with engine.connect() as conn:
        row = conn.execute(
            select(ConversationOwner.user_id).where(
                ConversationOwner.conversation_id == conversation_id
            )
        ).first()
    return row.user_id if row else None


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


def replace_passages(
    engine: Engine, source_refs: Iterable[str], records: list[PassageRecord]
) -> int:
    """Replace all passages for the given source documents, in one transaction.

    Deleting each document's existing passages before inserting the new ones makes
    re-ingest idempotent *and* orphan-free: chunks removed since a prior ingest
    (edited or shortened document) don't linger. Returns the inserted count.
    """
    refs = list(source_refs)
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
    with engine.begin() as conn:
        if refs:
            conn.execute(delete(Passage).where(Passage.source_ref.in_(refs)))
        if rows:
            conn.execute(insert(Passage).values(rows))
    return len(rows)


@dataclass(frozen=True)
class RegisterStats:
    register: str
    documents: int
    passages: int


def corpus_stats(engine: Engine) -> list[RegisterStats]:
    """Documents (distinct source_ref) and passages per register. Computed from passages."""
    sql = text(
        "SELECT register, count(DISTINCT source_ref) AS documents, count(*) AS passages "
        "FROM passages GROUP BY register ORDER BY register"
    )
    with engine.connect() as conn:
        return [RegisterStats(r.register, r.documents, r.passages) for r in conn.execute(sql)]


def search(engine: Engine, embedding: list[float], k: int) -> Sequence[Row]:
    """Return the k passages nearest `embedding` by cosine similarity (HNSW), score-first.

    `score` is cosine similarity in [0, 1] (1 = identical direction). Reads only.
    """
    vec_literal = "[" + ",".join(repr(float(x)) for x in embedding) + "]"
    stmt = text(
        "SELECT passage_id, text, register, category, document_title, locator, "
        "       1 - (embedding <=> CAST(:vec AS vector)) AS score "
        "FROM passages "
        "ORDER BY embedding <=> CAST(:vec AS vector) "
        "LIMIT :k"
    )
    with engine.connect() as conn:
        return conn.execute(stmt, {"vec": vec_literal, "k": k}).all()


def keyword_search(engine: Engine, terms: list[str], k: int) -> Sequence[Row]:
    """Passages whose text matches any of `terms` (case-insensitive). The escape hatch
    for exact-term lookups semantic search misses. Reads only; no score column."""
    if not terms:
        return []
    patterns = [f"%{t}%" for t in terms]
    stmt = text(
        "SELECT passage_id, text, register, category, document_title, locator "
        "FROM passages WHERE text ILIKE ANY(:patterns) LIMIT :k"
    )
    with engine.connect() as conn:
        return conn.execute(stmt, {"patterns": patterns, "k": k}).all()

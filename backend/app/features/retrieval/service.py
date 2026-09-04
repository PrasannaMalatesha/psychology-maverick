"""The `retrieval` service — semantic search over the passage store (ADR-0006).

Returns *scored* passages only; it does not decide grounded-vs-insufficient (that
policy is `chat`'s). Tested through a real pgvector store, never a fake.
"""

from dataclasses import dataclass

from sqlalchemy import Engine

from app.core.contracts import Category, Register
from app.core.llm.gateway import ModelGateway
from app.core.store import search


@dataclass(frozen=True)
class ScoredPassage:
    passage_id: str
    text: str
    register: Register
    category: Category | None
    document_title: str
    locator: str
    score: float


class RetrievalService:
    def __init__(self, engine: Engine, gateway: ModelGateway) -> None:
        self._engine = engine
        self._gateway = gateway

    def retrieve(self, query: str, k: int) -> list[ScoredPassage]:
        embedding = self._gateway.embed([query])[0]
        rows = search(self._engine, embedding, k)
        return [
            ScoredPassage(
                passage_id=row.passage_id,
                text=row.text,
                register=Register(row.register),
                category=Category(row.category) if row.category else None,
                document_title=row.document_title,
                locator=row.locator,
                score=float(row.score),
            )
            for row in rows
        ]

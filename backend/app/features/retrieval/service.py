"""The `retrieval` service — semantic search over the passage store (ADR-0006).

Returns *scored* passages only; it does not decide grounded-vs-insufficient (that
policy is `chat`'s). Tested through a real pgvector store, never a fake. Implemented
in T2/T3.
"""

from dataclasses import dataclass

from sqlalchemy import Engine

from app.core.contracts import Register
from app.core.llm.gateway import ModelGateway


@dataclass(frozen=True)
class ScoredPassage:
    passage_id: str
    text: str
    register: Register
    document_title: str
    locator: str
    score: float


class RetrievalService:
    def __init__(self, engine: Engine, gateway: ModelGateway) -> None:
        self._engine = engine
        self._gateway = gateway

    def retrieve(self, query: str, k: int) -> list[ScoredPassage]:
        raise NotImplementedError("retrieval.retrieve lands in T3 (uses T2's store)")

"""The `chat` service — the deep answer engine (ADR-0006).

Interface is one method, `answer(query) -> Answer`. It accepts its dependencies
(retrieval + the model gateway) rather than constructing them. The grounded-vs-
Insufficient-Context policy, citation assembly, and later safety nodes live behind
this interface. Implemented in T3 (grounded path) and T4 (insufficient + integrity).
"""

from app.core.llm.gateway import ModelGateway
from app.features.chat.schemas import Answer
from app.features.retrieval.service import RetrievalService


class ChatService:
    def __init__(self, retrieval: RetrievalService, gateway: ModelGateway) -> None:
        self._retrieval = retrieval
        self._gateway = gateway

    def answer(self, query: str) -> Answer:
        raise NotImplementedError("chat.answer grounded path lands in T3")

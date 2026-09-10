"""The `chat` feature service — thin entry over the agent (ADR-0005/0006).

`chat` owns the HTTP-facing `answer`/`history`; the LangGraph graph and its state
live in `assistant`. Keeps a small interface: `answer(query, conversation_id) -> Answer`.
"""

from __future__ import annotations

import uuid
from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from app.core.config import Settings
from app.core.llm.gateway import ModelGateway
from app.core.observability import Tracer
from app.features.assistant.service import AssistantService
from app.features.chat.schemas import Answer
from app.features.retrieval.service import RetrievalService


class ChatService:
    def __init__(
        self,
        retrieval: RetrievalService,
        gateway: ModelGateway,
        settings: Settings,
        tracer: Tracer | None = None,
        checkpointer: Any | None = None,
    ) -> None:
        # MemorySaver by default (in-process multi-turn); the app passes a Postgres saver.
        self._assistant = AssistantService(
            retrieval, gateway, settings, checkpointer or MemorySaver(), tracer
        )

    def answer(self, query: str, conversation_id: str | None = None) -> Answer:
        return self._assistant.answer(query, conversation_id or uuid.uuid4().hex)

    def review(self, conversation_id: str, decision: str) -> Answer:
        return self._assistant.resume(conversation_id, decision)

    def history(self, conversation_id: str) -> list[dict[str, Any]]:
        return self._assistant.history(conversation_id)

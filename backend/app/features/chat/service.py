"""The `chat` feature service — thin entry over the agent (ADR-0005/0006).

`chat` owns the HTTP-facing `answer`/`history`/`review`; the LangGraph graph and its state live
in `assistant`. Per-User ownership (M6) is recorded here when a `user_id` is supplied — the HTTP
layer always supplies one; direct (non-HTTP) callers may omit it, and then no owner is recorded.
"""

from __future__ import annotations

import uuid
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import Engine

from app.core.config import Settings
from app.core.llm.gateway import ModelGateway
from app.core.observability import Tracer
from app.core.store import get_conversation_owner, set_conversation_owner
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
        engine: Engine | None = None,
    ) -> None:
        # MemorySaver by default (in-process multi-turn); the app passes a Postgres saver.
        self._assistant = AssistantService(
            retrieval, gateway, settings, checkpointer or MemorySaver(), tracer
        )
        self._engine = engine  # None for direct callers that don't track ownership

    def answer(
        self, query: str, conversation_id: str | None = None, user_id: str | None = None
    ) -> Answer:
        conversation_id = conversation_id or uuid.uuid4().hex
        answer = self._assistant.answer(query, conversation_id)
        if user_id and self._engine is not None:
            set_conversation_owner(self._engine, conversation_id, user_id)
        return answer

    def review(self, conversation_id: str, decision: str) -> Answer:
        return self._assistant.resume(conversation_id, decision)

    def history(self, conversation_id: str) -> list[dict[str, Any]]:
        return self._assistant.history(conversation_id)

    def owner_of(self, conversation_id: str) -> str | None:
        """The User who owns this conversation, or None if unowned/untracked."""
        if self._engine is None:
            return None
        return get_conversation_owner(self._engine, conversation_id)

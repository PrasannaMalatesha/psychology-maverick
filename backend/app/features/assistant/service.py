"""AssistantService — compiles the agent graph with a checkpointer and runs it.

`answer` invokes the graph on a conversation's thread (multi-turn via the
checkpointer); `history` reads that thread's recorded turns.
"""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig

from app.core.config import Settings
from app.core.contracts import Answer
from app.core.llm.gateway import ModelGateway
from app.core.observability import NullTracer, Tracer
from app.features.assistant.agent import build_agent
from app.features.retrieval.service import RetrievalService


class AssistantService:
    def __init__(
        self,
        retrieval: RetrievalService,
        gateway: ModelGateway,
        settings: Settings,
        checkpointer: Any,
        tracer: Tracer | None = None,
    ) -> None:
        self._graph = build_agent(retrieval, gateway, settings).compile(checkpointer=checkpointer)
        self._tracer = tracer or NullTracer()

    def answer(self, query: str, conversation_id: str) -> Answer:
        config: RunnableConfig = {"configurable": {"thread_id": conversation_id}}
        with self._tracer.trace("chat.answer", query=query) as trace:
            config["configurable"]["trace"] = trace
            result = self._graph.invoke({"query": query}, config)
        return Answer.model_validate(result["answer"])

    def history(self, conversation_id: str) -> list[dict[str, Any]]:
        config: RunnableConfig = {"configurable": {"thread_id": conversation_id}}
        snapshot = self._graph.get_state(config)
        return snapshot.values.get("history", []) if snapshot and snapshot.values else []

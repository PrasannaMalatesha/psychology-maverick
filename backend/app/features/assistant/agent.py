"""The agent graph (ADR-0005: `assistant` owns the LangGraph graph/nodes/state).

M3 graph: retrieve → synthesize. State is JSON-plain (primitives only) so the
Postgres checkpointer can serialize it across turns. Nodes open trace spans via a
`trace` handle passed in the run config. M4 inserts crisis/faithfulness/HITL nodes
without reshaping this.
"""

from __future__ import annotations

import operator
from contextlib import nullcontext
from typing import Annotated, Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from app.core.config import Settings
from app.core.contracts import Answer, AnswerState, Category, Citation, Register
from app.core.llm.gateway import ModelGateway
from app.features.retrieval.service import RetrievalService, ScoredPassage


class AgentState(TypedDict):
    query: str
    passages: list[dict[str, Any]]
    answer: dict[str, Any] | None
    history: Annotated[list[dict[str, Any]], operator.add]


def _passage_dict(p: ScoredPassage) -> dict[str, Any]:
    """JSON-plain passage for AgentState (checkpointer serializes primitives only)."""
    return {
        "passage_id": p.passage_id,
        "text": p.text,
        "register": p.register.value,
        "category": p.category.value if p.category else None,
        "document_title": p.document_title,
        "locator": p.locator,
        "score": p.score,
    }


def _span(config: RunnableConfig, name: str):
    trace = config.get("configurable", {}).get("trace")
    return trace.span(name) if trace else nullcontext()


def build_agent(
    retrieval: RetrievalService, gateway: ModelGateway, settings: Settings
) -> StateGraph:
    def retrieve(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        with _span(config, "retrieve"):
            passages = retrieval.retrieve(state["query"], settings.retrieval_top_k)
        return {"passages": [_passage_dict(p) for p in passages]}

    def synthesize(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        query = state["query"]
        grounded = [p for p in state["passages"] if p["score"] >= settings.grounding_threshold]
        if not grounded:
            answer = Answer(state=AnswerState.insufficient_context)
        else:
            context = "\n\n".join(f"[{i + 1}] {p['text']}" for i, p in enumerate(grounded))
            with _span(config, "synthesize"):
                prose = gateway.synthesize(context=context, query=query)
            top_category = grounded[0]["category"]
            answer = Answer(
                state=AnswerState.grounded,
                category=Category(top_category) if top_category else None,
                text=prose,
                citations=[
                    Citation(
                        register=Register(p["register"]),
                        document_title=p["document_title"],
                        locator=p["locator"],
                        passage_id=p["passage_id"],
                    )
                    for p in grounded
                ],
            )
        answer_json = answer.model_dump(mode="json", by_alias=True)
        return {"answer": answer_json, "history": [{"query": query, "answer": answer_json}]}

    def keyword_tool(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        # Escape hatch: semantic search found nothing groundable; try exact-term lookup.
        merged = {p["passage_id"]: p for p in state["passages"]}
        with _span(config, "keyword_tool"):
            for sp in retrieval.keyword(state["query"], settings.retrieval_top_k):
                merged[sp.passage_id] = _passage_dict(sp)
        return {"passages": list(merged.values())}

    def grade(state: AgentState) -> str:
        strong = any(p["score"] >= settings.grounding_threshold for p in state["passages"])
        return "synthesize" if strong else "keyword_tool"

    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("keyword_tool", keyword_tool)
    graph.add_node("synthesize", synthesize)
    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges(
        "retrieve", grade, {"synthesize": "synthesize", "keyword_tool": "keyword_tool"}
    )
    graph.add_edge("keyword_tool", "synthesize")
    graph.add_edge("synthesize", END)
    return graph

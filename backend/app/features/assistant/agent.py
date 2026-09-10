"""The agent graph (ADR-0005: `assistant` owns the LangGraph graph/nodes/state).

Flow (M4): crisis_check → (crisis? finalize) → retrieve → grade → (keyword_tool?) →
synthesize → judge → review → finalize. State is JSON-plain (primitives only) so the
Postgres checkpointer can serialize it across turns. Nodes open trace spans via a
`trace` handle passed in the run config. The four ADR-0004 safety controls — crisis
routing, the faithfulness judge, the human-in-the-loop `review` interrupt, and the
clinical disclaimer — wrap the M3 retrieve/synthesize core without reshaping it.

`finalize` is the single point that appends the served answer to `history`: because the
judge and review steps can change the final answer, history must be recorded once, last.
"""

from __future__ import annotations

import operator
from contextlib import nullcontext
from typing import Annotated, Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.core.config import Settings
from app.core.contracts import Answer, AnswerState, Category, Citation, Register
from app.core.llm.gateway import ModelGateway
from app.features.assistant.safety import detect_crisis
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

    def crisis_check(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        # First gate (ADR-0004): acute-risk signal short-circuits to resources, before retrieval.
        with _span(config, "crisis_check"):
            if detect_crisis(state["query"]):
                answer = Answer(state=AnswerState.crisis, text=settings.crisis_resources)
                return {"answer": answer.model_dump(mode="json", by_alias=True)}
        return {}

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
            category = Category(top_category) if top_category else None
            answer = Answer(
                state=AnswerState.grounded,
                category=category,
                text=prose,
                # Clinical answers carry the "information, not advice" disclaimer (ADR-0004).
                disclaimer=settings.clinical_disclaimer if category is Category.clinical else None,
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
        return {"answer": answer.model_dump(mode="json", by_alias=True)}

    def judge(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        # Faithfulness judge (ADR-0004): a grounded answer its passages don't support is
        # downgraded to insufficient_context rather than shipped.
        answer = state["answer"]
        if answer and answer["state"] == AnswerState.grounded.value:
            grounded = [p for p in state["passages"] if p["score"] >= settings.grounding_threshold]
            context = "\n\n".join(p["text"] for p in grounded)
            with _span(config, "judge"):
                if not gateway.is_faithful(context=context, answer=answer["text"]):
                    downgraded = Answer(state=AnswerState.insufficient_context)
                    return {"answer": downgraded.model_dump(mode="json", by_alias=True)}
        return {}

    def review(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        # Human-in-the-loop (ADR-0004): a low-confidence *clinical* answer pauses for review.
        answer = state["answer"]
        is_clinical = (
            answer
            and answer["state"] == AnswerState.grounded.value
            and answer["category"] == Category.clinical.value
        )
        if is_clinical:
            scores = [
                p["score"] for p in state["passages"] if p["score"] >= settings.grounding_threshold
            ]
            top = max(scores) if scores else 0.0
            if top < settings.clinical_confidence_threshold:
                with _span(config, "review"):
                    decision = interrupt(
                        {"reason": "low-confidence clinical answer pending human review"}
                    )
                if decision != "approve":
                    withheld = Answer(
                        state=AnswerState.pending_review,
                        text="This answer was withheld pending human review.",
                    )
                    return {"answer": withheld.model_dump(mode="json", by_alias=True)}
        return {}

    def finalize(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        # Single history-append point: records the answer actually served (post judge/review).
        return {"history": [{"query": state["query"], "answer": state["answer"]}]}

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

    def crisis_route(state: AgentState) -> str:
        # crisis_check sets `answer` only on a crisis; otherwise proceed to retrieval.
        return "crisis" if state.get("answer") else "ok"

    graph = StateGraph(AgentState)
    graph.add_node("crisis_check", crisis_check)
    graph.add_node("retrieve", retrieve)
    graph.add_node("keyword_tool", keyword_tool)
    graph.add_node("synthesize", synthesize)
    graph.add_node("judge", judge)
    graph.add_node("review", review)
    graph.add_node("finalize", finalize)
    graph.add_edge(START, "crisis_check")
    graph.add_conditional_edges(
        "crisis_check", crisis_route, {"crisis": "finalize", "ok": "retrieve"}
    )
    graph.add_conditional_edges(
        "retrieve", grade, {"synthesize": "synthesize", "keyword_tool": "keyword_tool"}
    )
    graph.add_edge("keyword_tool", "synthesize")
    graph.add_edge("synthesize", "judge")
    graph.add_edge("judge", "review")
    graph.add_edge("review", "finalize")
    graph.add_edge("finalize", END)
    return graph

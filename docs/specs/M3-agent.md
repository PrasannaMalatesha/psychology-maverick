# Spec — M3: The Agent (LangGraph, tools, multi-turn)

**Status:** draft · **Milestone:** M3 (Build Sequence §15.3) · **Last updated:** 2026-09-07
**Builds on:** M1, M2. **Respects:** ADR-0002 (gateway), ADR-0005 (modular monolith; `assistant` = LangGraph graph/nodes/state), ADR-0006 (seams). Vocabulary per [CONTEXT.md](../../CONTEXT.md).

## Problem Statement

Today `chat.answer` is a single linear pass: embed → retrieve → threshold → synthesize. It has no
memory (every Query is standalone, so a follow-up like "and for children?" loses context) and no way
to recover when semantic retrieval misses an exact term the Corpus does use. The production design
(ADR-0005) calls for an **agent** — a LangGraph graph with state, tools, and a checkpointer — and the
current flow is not one.

## Solution

Turn the answer path into a **LangGraph `StateGraph`** whose state carries the Query, the running
conversation, retrieved passages, and the Answer. Persist that state with a **Postgres checkpointer**
keyed by conversation, so a follow-up Query continues the same thread. Add a **keyword/fetch tool** as
an escape hatch: when semantic retrieval scores are weak (or the Query is an exact-term lookup), the
graph fetches by keyword before synthesizing. The graph produces the same `Answer` contract as M1/M2,
so callers are unchanged except for an optional conversation id.

Nodes in scope: **retrieve → grade → (tool?) → synthesize.** Crisis-check, the faithfulness judge, and
human-in-the-loop are M4 and are deliberately not added here (the graph is structured so they slot in
later without reshaping it).

## User Stories

1. As a User, I want to ask a follow-up Query and have the assistant understand it in the context of my previous Queries, so that a conversation flows naturally.
2. As a User, I want each of my conversations kept separate, so that one thread's context never leaks into another.
3. As a User, I want the assistant to still find the right passage when I use an exact term semantic search alone would miss, so that precise questions aren't dropped to Insufficient Context.
4. As a User, I want a grounded Answer to keep citing its real passages whether they came from semantic search or the keyword tool, so that verifiability is unchanged.
5. As a User, I want to resume a conversation later and have it remembered, so that I don't restart from scratch.
6. As a User, I want to retrieve the history of a conversation, so that I can review what was asked and answered.
7. As a developer, I want the answer path expressed as a graph with explicit state and nodes, so that M4's safety nodes can be inserted without rewriting the flow.
8. As a developer, I want conversation state persisted by a checkpointer keyed on the conversation id, so that multi-turn works across processes, not just in memory.
9. As a developer, I want the keyword tool to be a graph node reached by a conditional edge (weak scores / exact-term), not an always-on path, so that the common case stays one hop.
10. As a developer, I want the graph to produce the same `Answer` contract, so that the HTTP adapter and its tests barely change.
11. As an operator, I want the checkpointer tables managed alongside the passage store setup, so that a fresh database is ready with one bootstrap.

## Implementation Decisions

- **New `assistant` feature** (ADR-0005 already names it) owns the LangGraph graph, nodes, and state.
  `chat.answer` becomes the thin entry that invokes the compiled graph and returns its `Answer`;
  `retrieval` and the gateway stay the graph's dependencies (injected).
- **Graph state** (typed): `query`, `conversation_id`, prior `messages`, `passages` (scored),
  `used_keyword_tool`, and the final `answer`. Nodes: `retrieve` (semantic top-k, M2), `grade`
  (decide if scores are strong enough or a keyword lookup is warranted), `keyword_tool` (fetch by term
  from the passage store), `synthesize` (grounded Answer from the collected passages, M1/M2 policy).
  A conditional edge after `grade` routes to `keyword_tool` or straight to `synthesize`.
- **Keyword tool** = a store query over passage `text` (SQL `ILIKE`/full-text) returning scored
  passages, merged with semantic results (dedup by `passage_id`). It is the ADR's documented
  escape hatch; reranking/embeddate upgrades stay future work.
- **Checkpointer:** `langgraph-checkpoint-postgres`, thread id = `conversation_id`. Its tables are
  created in the same bootstrap that runs `init_store`. Multi-turn = invoking the graph on the same
  thread; the checkpointer restores prior `messages`.
- **API:** `POST /chat` accepts an optional `conversation_id` (server generates one when absent and
  returns it). `GET /conversations/{id}` returns the conversation's turns from the checkpointer.
- **Answer contract unchanged** (M2 invariants still hold). Grounded Answers built from semantic +
  keyword passages; citations still resolve to real stored passages.
- **Gateway unchanged:** embeddings + synthesis still cross the one gateway seam; tests stub it.

## Testing Decisions

- **Seams:** the graph is exercised through `chat.answer` (service seam) and `POST /chat` (HTTP seam);
  the keyword tool and checkpointer run against **real pgvector/Postgres**; the model gateway is the
  one stub (**FakeGateway**). No test reaches inside the graph's nodes.
- **Prior art:** M1 `tests/test_chat.py`, `tests/test_insufficient.py`; M2 ingestion tests.
- **New coverage:** a follow-up Query on the same `conversation_id` sees prior context (multi-turn);
  two conversation ids stay isolated; a weak-semantic / exact-term Query routes through the keyword
  tool and still returns a grounded, cited Answer whose citations resolve to real passages;
  `GET /conversations/{id}` returns the recorded turns; grounded/insufficient behavior and the Answer
  contract are preserved through the graph.
- Tests assert structure, threading, and routing — not answer quality (that's M7 evals).

## Out of Scope

- Crisis-check, faithfulness judge, human-in-the-loop interrupts, disclaimers (M4).
- The model gateway registry/role-routing internals (M5); auth/RBAC and per-User conversation
  ownership (M6) — conversations here are keyed by id but not yet access-controlled; evals (M7);
  frontend (M8); deploy (M9).
- Reranking, Redis semantic cache (documented future upgrades).

## Further Notes

- Adds `langgraph` + `langgraph-checkpoint-postgres` as dependencies (the agent framework is now core).
- Real embeddings/synthesis still need their extras + backends; the whole graph is testable on the
  FakeGateway with real Postgres.
- Conversation history returned by `GET /conversations/{id}` is unauthenticated in M3; M6 puts it
  behind per-User ownership.

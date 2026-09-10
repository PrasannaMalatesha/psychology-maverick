# Spec — M4: Safety (crisis routing, faithfulness, human-in-the-loop, disclaimers)

**Status:** draft · **Milestone:** M4 (Build Sequence §15.4) · **Last updated:** 2026-09-10
**Builds on:** M1–M3. **Respects:** [ADR-0004](../adr/0004-informational-safety-posture.md) (non-negotiable safety posture), ADR-0005 (`assistant` owns the graph), ADR-0006 (seams). Vocabulary per [CONTEXT.md](../../CONTEXT.md).

**Gate:** no user-facing launch before this milestone. ADR-0004 is non-negotiable; a future maintainer must not loosen the posture.

## Problem Statement

The M3 agent answers every Query the same way: retrieve → grade → (tool?) → synthesize. It has no
notion of *safety*. A distressed user disclosing acute risk is answered as if they asked a factual
question; a synthesized answer that drifts from its passages ships unchecked; a low-confidence
*clinical* answer is served with no human in the loop; and clinical answers carry no disclaimer. The
corpus is mental-health-adjacent and some users arrive in crisis — ADR-0004 requires "safe by
construction", not a footnote.

## Solution

Insert four safety controls into the existing graph without reshaping the M3 flow (the graph was
built for exactly this):

1. **Crisis node, first.** Before retrieval, a conservative detector scans the Query for acute-risk
   signals (suicidal ideation, self-harm intent). On a hit the graph short-circuits: it surfaces
   crisis resources (US 988 + international `findahelpline.com`, config-driven / region-overridable)
   and stops. Safety takes priority over answering. Detection errs toward showing resources.
2. **Faithfulness judge.** After synthesis, a judge checks the grounded answer's prose is supported
   by its retrieved passages. If not, the answer is downgraded to `insufficient_context` rather than
   shipping an ungrounded claim. Grounding-by-construction (citations resolve to real passages)
   already holds from M1; the judge adds a runtime check on the free text.
3. **Human-in-the-loop interrupt.** A grounded, *clinical*-category answer whose top passage score
   is below a confidence threshold pauses the graph (LangGraph `interrupt`) for human review instead
   of auto-serving. A reviewer resumes with approve (serve it) or reject (withhold).
4. **Clinical disclaimer.** Grounded answers in the `clinical` Category carry a disclaimer: general
   information from published sources, not medical advice or diagnosis.

The `Answer` contract gains two states (`crisis`, `pending_review`) and an optional `disclaimer`.
Callers are otherwise unchanged; a new `POST /conversations/{id}/review` resumes an interrupted turn.

## User Stories

1. As a distressed User, when I disclose that I want to harm myself, I want the assistant to show me
   crisis resources and stop, rather than answer me like a search engine, so that safety comes first.
2. As a User, I want the assistant to refuse to ship an answer its own sources don't support, so that
   a fluent-but-ungrounded reply never reaches me.
3. As a User asking something clinical where the evidence is weak, I want a human to review before an
   answer is served, so that borderline clinical guidance isn't automated onto me.
4. As a User reading a clinical answer, I want a plain disclaimer that this is information and not
   medical advice, so that I know its limits.
5. As a reviewer, I want to approve or reject a held clinical answer and have the conversation resume,
   so that human judgment closes the loop.
6. As a developer, I want the four controls added as graph nodes/edges around the M3 flow, so that the
   agent's shape is unchanged and each control is independently testable.
7. As a developer, I want crisis detection and the faithfulness judge behind seams (a pure function;
   the model gateway), so that the whole milestone is testable offline on FakeGateway + real Postgres.
8. As an operator, I want the crisis resources, disclaimer text, and confidence threshold to be
   configuration, so that they are tuned without code changes and overridable per region.

## Implementation Decisions

- **Crisis detection is a deterministic, conservative matcher** (`assistant/safety.py`,
  `detect_crisis(text) -> bool`): a curated set of acute-risk phrases, case-insensitive, word-boundary
  matched. No model call — it must run before retrieval on every Query and be deterministic in tests.
  It intentionally over-triggers (ADR-0004's accepted trade-off). *Upgrade to an LLM/classifier is
  M7 (evals) territory; the seam is a single function so swapping it is local.*
- **Crisis is an `AnswerState`.** `crisis` carries the resources text, no category/citations/
  disclaimer. The `crisis_check` node sets it and routes straight to `finalize` (skipping retrieval).
- **Faithfulness is a gateway capability.** `ModelGateway.is_faithful(*, context, answer) -> bool` —
  `ProductionGateway` uses an LLM yes/no judge (lazy, `synthesis` extra); `FakeGateway` returns
  `True` deterministically. A `judge` node runs after `synthesize`; on `False` for a grounded answer
  it overwrites the answer with `insufficient_context`.
- **HITL uses LangGraph `interrupt`.** A `review` node after `judge`: for a grounded `clinical`
  answer with top grounded score `< clinical_confidence_threshold`, it calls `interrupt(...)`. Resume
  value `"approve"` serves the answer; anything else withholds it as `pending_review`. Wired through
  `AssistantService.resume(conversation_id, decision)` and `POST /conversations/{id}/review`.
- **History moves to a single `finalize` node.** M3 appended history inside `synthesize`; because the
  judge and review steps can change the final answer, history is now appended once, in `finalize`, so
  it always records the answer actually served. `crisis_check` routes to `finalize` too.
- **Disclaimer is an optional `Answer.disclaimer`.** Set in `synthesize` when the grounded answer's
  Category is `clinical`. Other states carry no disclaimer (contract-enforced).
- **Config (ADR-0002):** `crisis_resources: str`, `clinical_disclaimer: str`,
  `clinical_confidence_threshold: float` (default tuned for production; the shared test fixture sets
  it to `0.0` so only the dedicated HITL test opts in, mirroring how `grounding_threshold` is handled).

### Graph (after M4)

```
START → crisis_check ─(crisis)→ finalize → END
                     └─(ok)→ retrieve → grade ─(strong)→ synthesize
                                              └─(weak)→ keyword_tool → synthesize
        synthesize → judge → review → finalize → END
```

## Testing Decisions

- **Seams unchanged:** exercised through `chat.answer` / `AssistantService` (service seam) and
  `POST /chat` + `POST /conversations/{id}/review` (HTTP seam), against **real pgvector/Postgres**;
  the model gateway is the one stub (**FakeGateway**), sub-classed where a test needs an unfaithful
  judge. No test reaches inside a node.
- **New coverage:**
  - a crisis-phrase Query returns `state=crisis` with resources text, **no retrieval/citations**, and
    a non-crisis Query is unaffected;
  - an unfaithful judge (stub gateway → `False`) downgrades a would-be-grounded answer to
    `insufficient_context`;
  - a low-confidence clinical Query (`clinical_confidence_threshold` forced high) interrupts →
    `pending_review`; `review` with `approve` serves the grounded, cited answer; with `reject`
    withholds it;
  - a grounded clinical answer carries the disclaimer; the crisis/insufficient states carry none;
  - all M3 behavior (multi-turn, isolation, keyword tool, history, contract) still holds.
- Tests assert routing, states, and threading — not answer quality (M7 evals).

## Out of Scope

- LLM/classifier-based crisis detection and a tuned faithfulness rubric (M7 evals refine both).
- A reviewer UI / queue and auth on the review endpoint (M8 frontend, M6 auth — the endpoint is
  unauthenticated in M4, like `GET /conversations/{id}` in M3).
- Model registry / role routing (M5); per-User ownership (M6); deploy (M9).

## Further Notes

- No new runtime dependency: `interrupt`/`Command` ship with `langgraph`; the faithfulness judge
  reuses the existing `synthesis` extra (LiteLLM). Crisis detection is stdlib `re`.
- The interrupt path needs a checkpointer (it already exists from M3); an interrupted turn records no
  history until it is resolved.

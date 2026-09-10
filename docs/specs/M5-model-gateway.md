# Spec — M5: Config-driven model gateway (LiteLLM roles + fallback)

**Status:** draft · **Milestone:** M5 (Build Sequence §15.5) · **Last updated:** 2026-09-10
**Builds on:** M1–M4. **Respects:** [ADR-0002](../adr/0002-config-driven-model-gateway.md) (config-driven multi-provider gateway), ADR-0006 (the gateway is the one real seam). Vocabulary per [CONTEXT.md](../../CONTEXT.md).

## Problem Statement

`ProductionGateway` calls LiteLLM with a single flat `synthesis_model`, and embeds only with a
hard-wired local model. There is no notion of *logical roles*, no way to route cheap work to a cheap
model and synthesis to a premium one, and no fallback when a provider is down or repriced — the exact
thing ADR-0002 says the gateway exists to provide. Swapping a model is a code edit, not a config
change.

## Solution

Introduce a **role registry in configuration**: the logical roles the code actually uses —
`synthesizer`, `judge`, `embedder` — each map to a primary model plus an ordered fallback chain. The
gateway routes each capability to its role's chain and tries models in order (`_complete`): the first
success wins; a provider/transport error falls through to the next; if all fail, the last error is
surfaced. The `embedder` role additionally distinguishes a `local/<id>` model (local
sentence-transformers) from a remote LiteLLM embedding model, and guards the output dimensionality
against the store's fixed `EMBEDDING_DIM`. FakeGateway is unchanged, so the whole suite stays offline.

## User Stories

1. As an operator, I want to swap or add a model per role by editing configuration, so that provider
   changes never require a code change.
2. As an operator, I want cheap models on cheap work (judging) and a premium model on synthesis, so
   that cost tracks value.
3. As an operator, I want a role to fall back to another model when its primary fails, so that one
   provider outage doesn't take the assistant down.
4. As a developer, I want the routing and fallback logic tested deterministically without live model
   calls, so that CI stays offline and fast.
5. As a developer, I want a remote embedder that returns the wrong dimensionality to fail loudly, so
   that a misconfiguration can't silently corrupt the passage store.

## Implementation Decisions

- **Roles live in `Settings` as nested `ModelRole` models** (`primary` + `fallbacks`), with defaults
  per project.md §6 (synthesizer → a premium model, judge → a cheap flash model, embedder → local
  bge). Config-driven per ADR-0002 **without** adding a YAML file or loader (pydantic settings are the
  config surface; a role is env-overridable as JSON). *A separate YAML registry is deferred — nothing
  needs it yet.*
- **One router, `_complete(chain, call)`** (module-level in `production_gateway`): iterates the role's
  chain, returns the first `call(model)` that doesn't raise, else raises `RuntimeError` chaining the
  last error. `synthesize`/`is_faithful`/`embed` each build a `call` closure and hand it their role's
  chain. Routing (T1) is just a length-1 chain, so routing and fallback (T2) are one implementation.
- **Embedder routing (T3):** a `local/<id>` primary uses local sentence-transformers (cached per id);
  any other id uses `litellm.embedding`. Output dim is asserted equal to `EMBEDDING_DIM`; a mismatch
  raises rather than writing a corrupt vector.
- **`grader` role omitted:** the graph's `grade` step is a score threshold, not a model call, so there
  is no LLM grader to route. Adding one would be speculative.
- **LiteLLM / sentence-transformers stay lazy-imported** behind the `synthesis` / `embeddings` extras;
  the module imports cleanly without them, and tests never load them.

## Testing Decisions

- **Offline and pure:** the router (`_complete`) and role `chain` are unit-tested with injected call
  functions — primary-only success, fall-through to the first working fallback, all-fail raises. The
  embedder dim guard is tested by stubbing the local model to emit right- and wrong-dim vectors. No
  container, no provider key, no network.
- **Seam unchanged:** every existing service/HTTP test still runs on FakeGateway; M5 changes only
  `ProductionGateway` internals and the `Settings` role fields, which no test depends on by name.
- Fallback *behaviour across real providers* (answer-quality drift, per ADR-0002's caveat) is a
  live-run / M7-evals concern, not asserted here.

## Out of Scope

- A standalone YAML/JSON registry file and hot-reload (deferred; pydantic config covers today's need).
- An LLM `grader` role (no LLM grader exists).
- Real multi-provider fallback verification — only a Gemini key is available; the mechanism is tested,
  the live story is as real as the keys present (ADR-0002).
- Per-role tracing/cost accounting (Langfuse/observability deepening is M7).

## Further Notes

- No new dependency: LiteLLM already backs synthesis; `litellm.embedding` is the same package.
- Changing the embedder to a different-dimension model is a store migration (the pgvector column is
  fixed at `EMBEDDING_DIM`) — the dim guard turns that from silent corruption into a clear failure.

# Deep-module seams: small feature-service interfaces, one gateway seam

Within the modular monolith ([ADR-0005](0005-modular-monolith-vertical-slices.md)), every feature is
designed as a **deep module**: a lot of behaviour behind a **small interface** (its public service).
The interface — not the implementation size — is what we keep small. Callers and tests cross the
same interface; nothing reaches past it.

Concretely, for the backend:

- **A feature's public service is its interface.** `chat` exposes essentially `answer(query) -> Answer`;
  `corpus` exposes `ingest(source) -> IngestReport`; `retrieval` exposes `retrieve(query, k) -> ScoredPassage[]`.
  Everything else in the feature — routers, repository, chunking, SQL, pgvector calls — is
  **implementation** behind that interface.
- **Answer *policy* lives in `chat`, not in retrieval.** `retrieval.retrieve()` returns scored
  passages and nothing more; the grounded-vs-**Insufficient Context** threshold decision, citation
  assembly, and (later) crisis-check and the faithfulness judge are `chat`'s implementation. New
  safety behaviour ([ADR-0004](0004-informational-safety-posture.md)) slots in behind `answer()`
  without changing its interface.
- **Repositories are internal, not swappable seams.** Each feature owns a repository (ADR-0005), but
  it is implementation detail behind the service — there is no second adapter for it. We test it
  through a **real ephemeral Postgres + pgvector**, never a fake. (One adapter is a *hypothetical*
  seam; we don't introduce the abstraction until something varies across it.)
- **The LiteLLM gateway (`core/llm`) is the one real seam.** It has **two adapters** — the real
  provider-routing adapter ([ADR-0002](0002-config-driven-model-gateway.md)) and a deterministic
  test double — so it is a genuine seam. It is the single dependency substituted in tests; embedding
  and synthesis calls are the only nondeterministic, cost-bearing boundary, and they all cross here.

## Why

- **Leverage + locality.** A small `answer(query)` interface pays back across every caller and every
  test, and concentrates change: adding the faithfulness judge is one edit inside `chat`, invisible
  to callers. **Deletion test:** delete `chat`'s service and the retrieve→threshold→synthesize→cite
  pipeline reappears in the HTTP handler and every test — it earns its keep. Delete a hypothetical
  repository abstraction and nothing reappears — so we don't build it.
- **The interface is the test surface.** Tests cross exactly the seams callers do: HTTP over `chat`,
  the CLI over `corpus.ingest`, the gateway double, and real pgvector for `retrieval`. If we ever
  wanted to test *past* one of these interfaces, that module would be the wrong shape.
- **Testability falls out of the shapes.** Services **accept their dependencies** (`chat.answer`
  receives `retrieval` + the gateway; `corpus.ingest` receives the gateway) rather than constructing
  them, and **return results** rather than mutating shared state (the only writes are ingestion's
  explicit upserts).

## Consequences

- The gateway interface is defined once, in `core/llm`, with a real adapter and a fake; features
  depend on the interface, never on a provider SDK directly.
- Feature services are the only cross-feature entry points (ADR-0005); no feature reaches into
  another's repository or internals.
- Interfaces are provisional until first use proves them; when an interface is genuinely hard to
  settle, design it more than once before committing (see the codebase-design skill's design-it-twice).

## Status

Accepted (2026-09-03). First applied by the M1 slice ([docs/specs/M1-rag-chat-slice.md](../specs/M1-rag-chat-slice.md)):
T1 establishes the gateway seam + the thin HTTP/health adapter + the feature shells; later tickets fill
each service behind its interface, and #4/#5 add behaviour without changing any interface.

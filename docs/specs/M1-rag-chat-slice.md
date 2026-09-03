# Spec — M1 Vertical Slice: Grounded, Cited `/chat`

**Status:** ready-for-agent · **Milestone:** M1 (Build Sequence §15.1) · **Last updated:** 2026-09-03
**Respects:** ADR-0001 (single Postgres + pgvector), ADR-0002 (config-driven model gateway), ADR-0005 (modular monolith / vertical slices), ADR-0004 (informational-only safety posture — see Out of Scope). Vocabulary per [CONTEXT.md](../../CONTEXT.md).

> Publishing note: no issue tracker / triage vocabulary was configured for the authoring session, so this spec is committed as a document rather than a tracker issue. When a tracker is set up (`/setup-matt-pocock-skills`), file this with the `ready-for-agent` triage label.

---

## Problem Statement

Today the Knowledge Assistant only *looks* real. Both the canonical prototype and the divergent fork answer a Query with a small hard-coded keyword matcher — there is no Corpus retrieval, no real Answer, and no Citation that resolves to actual source material. A person cannot ask a genuine psychology question and trust that the reply came from, and points back to, the curated Corpus. Nothing exercises the production spine (retrieve → synthesize → observe), so none of the architecture decisions have been proven end to end.

## Solution

Build the thinnest real slice of the backend that proves the spine end to end: an offline ingestion path that loads a *subset* of the Corpus into a single Postgres database with pgvector, and a real `POST /chat` request path that takes a Query, retrieves the most relevant Corpus passages, and synthesizes a grounded Answer whose every Citation resolves to a retrieved passage. When the Corpus does not cover the Query, the Assistant returns Insufficient Context instead of inventing an Answer. Each Query emits one Langfuse trace spanning retrieval and synthesis, so the behavior is observable. This replaces the canned matcher with the real mechanism, at the smallest scope that is honestly end to end.

## User Stories

1. As a User, I want to ask a psychology Query in plain language and receive a grounded Answer, so that I learn something trustworthy rather than a plausible-sounding guess.
2. As a User, I want every Answer to carry Citations back to the specific Corpus passages that support it, so that I can verify the claim at its source.
3. As a User, I want each Citation to name its register (textbook, research, or consumer health), so that I can weigh how authoritative the support is.
4. As a User, I want the Assistant to say it has Insufficient Context when my Query falls outside the Corpus, so that I am never handed a fabricated Answer.
5. As a User, I want an Answer that is visibly derived only from the retrieved passages, so that I can trust the Assistant is not free-inventing beyond its sources.
6. As a User, I want a Query about a covered topic to reliably find the relevant material even if I phrase it loosely, so that I do not have to guess the Corpus's exact wording.
7. As a User, I want the Answer tagged with its Category (e.g. cognitive, social, clinical, developmental), so that I understand which subfield the material comes from.
8. As a User, I want a Citation to point at a stable, resolvable passage identity, so that following it always lands on the same supporting text.
9. As a User, I want an Answer to a genuinely out-of-domain Query (e.g. car repair) to return Insufficient Context, so that the Assistant stays honest about its boundaries.
10. As a User, I want a Query the Corpus only weakly touches to return Insufficient Context rather than a thinly-supported Answer, so that low-confidence grounding never masquerades as fact.
11. As an Admin, I want to ingest a subset of the Corpus from the source PDFs via a command-line tool, so that I can populate the Assistant's knowledge without a manual database step.
12. As an Admin, I want ingestion to chunk source material with respect to its structure (chapter/section for the textbook, article structure for research), so that retrieved passages are coherent units rather than arbitrary slices.
13. As an Admin, I want each ingested passage to carry its register, Category, and section metadata, so that Citations and later evaluations can be sliced by those attributes.
14. As an Admin, I want ingestion to be idempotent and re-runnable over the subset, so that re-ingesting does not duplicate passages or corrupt the store.
15. As an Admin, I want embeddings computed in batches during ingestion, so that loading the subset is efficient and does not exhaust rate limits.
16. As an Admin, I want ingestion to record which source documents and how many passages were loaded, so that I can confirm the Corpus subset landed as expected.
17. As an operator, I want one Langfuse trace per Query that shows the retrieval step and the synthesis step, so that I can see and debug the spine end to end.
18. As an operator, I want the model and embedding calls to route through the configured gateway, so that swapping or falling back a model is a config change, not a code change.
19. As an operator, I want a `GET /health` endpoint, so that I can confirm the service and its database are reachable.
20. As an operator, I want the retrieval depth (top-k) and the grounding threshold to be configuration, so that I can tune precision versus recall without redeploying logic.
21. As a developer, I want the `chat` and `corpus` concerns to live as separate vertical slices with enforced boundaries, so that the M1 spine can grow into the full agent without a rewrite.
22. As a developer, I want the Answer contract expressed as a typed schema shared by the request path and the tests, so that the API shape is unambiguous and stable.
23. As a developer, I want the synthesis boundary to be the single place external model calls happen, so that tests can substitute a deterministic double there and nowhere else.
24. As a developer, I want retrieval to run against a real pgvector index in tests, so that similarity behavior is actually exercised rather than mocked away.
25. As a future maintainer, I want the `/chat` contract shaped so streaming can be added without breaking clients, so that the eventual SSE upgrade is additive.
26. As a safety reviewer, I want M1 explicitly marked as an internal spine proof that is not user-facing until the Safety milestone lands, so that a Corpus-answering endpoint without Crisis Escalation is never exposed to real users.

## Implementation Decisions

**Architecture & modules.** Two vertical slices in the modular monolith (ADR-0005), boundaries enforced by `import-linter` in CI:
- **`corpus`** — owns the offline ingestion CLI: PDF parsing, structure-aware chunking, metadata attachment, batched embedding, and persistence. Ingestion is a CLI, never an HTTP endpoint.
- **`chat`** — owns `POST /chat`: the retrieve → synthesize request path and the Answer contract. `GET /health` lives at the app boundary.

**Storage (ADR-0001).** A single Postgres database (Neon) holds both relational rows and vector embeddings via pgvector with an HNSW index. Passages (chunks) store: text, embedding vector, register, Category, section/locator metadata, source-document reference, and a stable passage identity. No separate vector database; no Redis in M1.

**Models (ADR-0002).** All model and embedding calls route through the config-driven LiteLLM gateway with role-based routing and fallback. M1 uses two roles: an **embedding** role (default `bge-small-en-v1.5`, 384-dim) and a **synthesis** role. Model choice is registry/config, not inline code.

**Ingestion (offline CLI).** Parse the source PDFs of a Corpus *subset* → structure-aware chunking (respect chapter/section and article structure; size-capped with small overlap) → attach `register` / `category` / section metadata → batch-embed → upsert into Postgres. Idempotent on re-run (stable passage identity prevents duplication). Emits a summary of documents and passage counts.

**Retrieval (request path).** Embed the Query via the gateway, then semantic top-k retrieval (default **k = 5**) over the HNSW index. Keyword/fetch tools, reranking, and the semantic cache are deferred to later milestones. A grounding threshold governs the Insufficient Context decision: if no retrieved passage clears the threshold, the path returns Insufficient Context without calling synthesis.

**Synthesis & grounding.** When retrieval yields qualifying passages, the synthesis role produces an Answer strictly from those passages; the prompt constrains the model to the retrieved context and to emitting Citations only for passages it used. Every Citation in a returned Answer must correspond to a passage that was actually retrieved for that Query — no Citation may reference a passage outside the retrieved set.

**Answer contract (typed schema, shared by request path and tests).** Encodes the grounding decision precisely:

```
Answer
  state:      "grounded" | "insufficient_context"
  category:   Category | null          # null when insufficient_context
  text:       string | null            # grounded prose; null when insufficient_context
  citations:  Citation[]               # non-empty when grounded; empty when insufficient_context

Citation
  register:        "textbook" | "research" | "consumer_health"
  document_title:  string
  locator:         string              # chapter/section (textbook) or article locator (research/consumer)
  passage_id:      string              # stable id of a retrieved corpus passage
```

`Category` is the existing fixed enum from the glossary. A `grounded` Answer has non-empty `text` and at least one `Citation`; an `insufficient_context` Answer has null `text`, null `category`, and no `citations`.

**API contract.** `POST /chat` accepts a Query and returns a complete `Answer` as JSON in M1. The contract is shaped so that SSE streaming of the same `Answer` can be added later without a breaking change (streaming itself is out of scope for M1). `GET /health` returns service + database reachability.

**Observability.** Each Query emits exactly one Langfuse trace with, at minimum, a retrieval span and a synthesis span (the synthesis span absent when the path short-circuits to Insufficient Context). Tracing is PII-aware per project security notes.

**Configuration.** top-k, grounding threshold, model roles, and connection details are environment/config-driven, with a committed `.env.example`.

## Testing Decisions

**What a good test is here.** Tests assert *observable external behavior* — what a caller of `POST /chat` or the ingestion CLI sees — never internal function shapes, private helpers, or prompt wording. This mirrors the philosophy of the existing Playwright suite (46/46, desktop + mobile), which is the project's prior art for black-box behavior testing; M1 applies the same stance one layer down, at the API and CLI seams.

**Seams (confirmed with the developer).** The fewest, highest seams:
- **Primary seam — `POST /chat` (HTTP).** Black-box tests drive the whole retrieve → synthesize spine through the real endpoint.
- **Secondary seam — the ingestion CLI.** Tests invoke the CLI on fixture source material and assert the resulting Corpus state.
- **The single stubbed boundary — the model gateway.** Embedding and synthesis calls through the LiteLLM gateway are replaced by deterministic doubles / recorded fixtures, so tests are offline, deterministic, and free. This is the *only* place a test double is injected.
- **Real pgvector.** Retrieval runs against a real ephemeral Postgres + pgvector test database, seeded with a tiny fixture Corpus spanning all three registers. The vector store is never mocked, so similarity behavior is genuinely exercised.

**Modules tested.** `chat` (via HTTP) and `corpus` (via CLI). No direct unit tests of chunking or retrieval internals — they are covered through the two seams above.

**Behaviors to assert (representative, not exhaustive).**
- A Query covered by the seeded Corpus returns a `grounded` Answer with at least one Citation, and every returned `passage_id` resolves to a passage actually present in the seeded Corpus.
- A Query outside the Corpus returns `insufficient_context` with null `text` and no Citations — and the synthesis double is never invoked (the threshold short-circuits before synthesis).
- No returned Citation references a passage outside the set retrieved for that Query (no fabricated Citations).
- Retrieval returns at most top-k passages, ordered by similarity, for a covered Query.
- The ingestion CLI over fixture material produces the expected passages with correct `register`, `category`, and section metadata, and re-running it does not duplicate passages (idempotency).
- Exactly one Langfuse trace is produced per Query, carrying a retrieval span (and a synthesis span when the Answer is grounded) — asserted at the trace boundary.
- `GET /health` reports healthy when the database is reachable.

## Out of Scope

- **Crisis Escalation, Faithfulness judge, Human-in-the-loop, clinical disclaimers** — the entire Safety milestone (Build Sequence §15.4, ADR-0004). M1 is not user-facing precisely because these are absent (see Further Notes).
- **The full agent** — LangGraph node graph, tool-calling / keyword-fetch tools, multi-turn, Postgres checkpointer (§15.3).
- **Auth & security hardening** — JWT, RBAC, per-User conversation ownership (§15.6). M1 has no authenticated Users yet.
- **SSE streaming** of the Answer — the contract is shaped to allow it, but streaming is not implemented in M1.
- **Reranking (cross-encoder) and the Redis semantic cache** — documented upgrades, later.
- **Full Corpus ingestion** — M1 ingests a subset only.
- **Frontend wiring** — connecting either the fork UI or the canonical Next.js frontend to the real endpoint is a separate spec; the M1 contract is deliberately frontend-agnostic.
- **Deployment** to Render / Vercel / Upstash / Langfuse Cloud (§15.9).
- **Evaluation suite and CI quality gate** (§15.7).

## Further Notes

- **Safety gate (non-negotiable).** M1 delivers a Corpus-answering `/chat` that has no Crisis Escalation and no Faithfulness judge. It is an *internal spine proof* whose success criterion is "one Langfuse trace visible," not "shipped to users." It must not be exposed to real Users until the Safety milestone lands, because a mental-health endpoint without crisis handling violates ADR-0004. This constraint belongs in the merge/deploy checklist, not just here.
- **Frontend decision still open.** The build target for the eventual UI (the polished fork vs. the canonical MindMarket Next.js app) is unresolved and does not block M1; the API contract is designed so either can consume it later.
- **Database provisioning.** The Neon Postgres + pgvector connector was available in the authoring session, so the dev/test database (ADR-0001) can be stood up without leaving the tooling. Provisioning the remaining accounts (Upstash, Langfuse, Render, Vercel) remains the developer's task and is not required for M1.
- **Vocabulary.** Use the glossary terms throughout the implementation and its tests — Query, Answer, Corpus, Citation, Category, Insufficient Context, Faithfulness, User, Admin — and avoid the deprecated synonyms listed in CONTEXT.md.

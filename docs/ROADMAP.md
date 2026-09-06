# Build Roadmap — Psychology Maverick

**A living tracker so the 9 build milestones never get lost.** Update the Status column as work lands.

- **Plan / source of truth:** [project.md §15](../project.md) (build sequence), [docs/PRD.md](PRD.md) (product), [docs/adr/](adr/) (decisions), [CONTEXT.md](../CONTEXT.md) (glossary).
- **How milestones get built:** each one gets its own spec via `/to-spec` → filed as a GitHub issue with the `ready-for-agent` label → built → checked off here. One spec = one buildable slice; there is intentionally **no single spec for the whole app**.
- **Status legend:** ⬜ not started · 🟡 spec written · 🔵 in progress · ✅ done

| M | Milestone | Scope (one line) | Spec | Issue | Status |
|---|-----------|------------------|------|-------|:---:|
| **M1** | Vertical slice | Ingest a corpus *subset* → real `POST /chat` (retrieve → synthesize) → one Langfuse trace. Proves the spine. | [M1-rag-chat-slice.md](specs/M1-rag-chat-slice.md) | [#1](https://github.com/PrasannaMalatesha/psychology-maverick/issues/1)–[#5](https://github.com/PrasannaMalatesha/psychology-maverick/issues/5) | ✅ |
| **M2** | Contracts & storage | Full `Answer` contract (invariants), Category on every passage, JSON reader, whole-corpus ingestion + corpus stats. | [M2-contracts-and-storage.md](specs/M2-contracts-and-storage.md) | [#7](https://github.com/PrasannaMalatesha/psychology-maverick/issues/7)–[#9](https://github.com/PrasannaMalatesha/psychology-maverick/issues/9) | 🔵 |
| **M3** | Agent | LangGraph node graph, tool-calling (keyword/fetch), Postgres checkpointer, multi-turn conversations. | — | — | ⬜ |
| **M4** | Safety *(non-negotiable — [ADR-0004](adr/0004-informational-safety-posture.md))* | Crisis-escalation node (before retrieval), faithfulness judge, human-in-the-loop interrupt, clinical disclaimers. **Gate: no user-facing launch before this.** | — | — | ⬜ |
| **M5** | Model gateway | LiteLLM registry, role-based routing + fallback across the full model set ([ADR-0002](adr/0002-config-driven-model-gateway.md)). | — | — | ⬜ |
| **M6** | Auth & security | Email+password JWT (argon2, refresh rotation, Redis revocation), user/admin RBAC, per-User conversation ownership. | — | — | ⬜ |
| **M7** | Evals & CI gate | Offline evaluation suite (faithfulness, retrieval quality) + CI quality gate + `import-linter` boundary checks. | — | — | ⬜ |
| **M8** | Frontend | Chat + citations + trust states + auth + sidebar, on the chosen frontend (see open decision below). | — | — | ⬜ |
| **M9** | Deploy | Compose → Render (FastAPI) + Neon (Postgres) + Upstash (Redis) + Vercel + Langfuse Cloud ([ADR-0003](adr/0003-hybrid-deployment.md)). | — | — | ⬜ |

### M1 tickets (build in order; live status on GitHub)

Work the frontier — a ticket is grabbable once its blockers are ✅.

- [x] [#1](https://github.com/PrasannaMalatesha/psychology-maverick/issues/1) **T1** Walking skeleton: backend + `/health` + test seams — ✅ done (ruff/pyright/pytest/import-linter green)
- [x] [#2](https://github.com/PrasannaMalatesha/psychology-maverick/issues/2) **T2** Corpus ingestion CLI + passage store — ✅ done (10/10 tests, gate green)
- [x] [#3](https://github.com/PrasannaMalatesha/psychology-maverick/issues/3) **T3** Grounded, cited `POST /chat` (happy path) — ✅ done (12/12 tests, gate green)
- [x] [#4](https://github.com/PrasannaMalatesha/psychology-maverick/issues/4) **T4** Insufficient Context + no-fabrication guarantee — ✅ done (16/16 tests, gate green)
- [x] [#5](https://github.com/PrasannaMalatesha/psychology-maverick/issues/5) **T5** One Langfuse trace per Query — ✅ done (18/18 tests, gate green)

**M1 complete** ✅ — all 5 tickets landed; the canned matcher is gone, the real retrieve→synthesize spine is proven end to end.

### M2 tickets (build in order; live status on GitHub)

- [ ] [#7](https://github.com/PrasannaMalatesha/psychology-maverick/issues/7) **T1** JSON/PLOS reader + Category on every passage — *blocked by: none*
- [ ] [#8](https://github.com/PrasannaMalatesha/psychology-maverick/issues/8) **T2** `Answer` contract invariants (+ bge threshold default) — *blocked by: none*
- [ ] [#9](https://github.com/PrasannaMalatesha/psychology-maverick/issues/9) **T3** Corpus stats + robust whole-corpus ingest — *blocked by: #7*

Post-M1 fixes on `dev` (from `/code-review`):
- **2026-09-06** — Orphan passages on re-ingest fixed: ingestion now **replaces** each document's passages in one transaction (`core/store.replace_passages`), so chunks removed from an edited/shortened document no longer linger. 19/19 tests (added a shortened-re-ingest orphan check). Still open (deferred to M2/M7): grounded-answer null category from PDFs lacking category metadata; `grounding_threshold` calibration for bge (~0.55 per the live run); LangfuseTracer v2-vs-v3 API pin.

**Definition of v1 / MVP:** M1–M9 together — a real User can sign in, ask a Query, and get a safe, grounded, cited Answer in a deployed UI. M1 alone is an *internal spine proof*, not a shippable product.

## Open decisions (resolve before the milestone they block)

- **Frontend target (blocks M8):** the ADRs assume a **Next.js** app on the **MindMarket** design system (this canonical repo). The polished session work lives on a **divergent fork** (Vite/React, DM fonts, DSM-5 + freemium + editorial redesign). Decide whether M8 builds the canonical Next.js frontend or adopts/ports the fork. The M1–M7 backend is frontend-agnostic, so this does not block them.
- **Provisioning (blocks M9, partially M1 dev):** Neon is reachable via connector; Upstash, Langfuse, Render, Vercel accounts are the owner's task.

## Progress log

- **2026-09-03** — Repo scaffolded + pushed to GitHub (`PrasannaMalatesha/psychology-maverick`, public). Agent-skill config + triage labels set up. M1 spec written and broken into 5 `ready-for-agent` tickets (#1–#5). ADR-0006 (deep-module seams) added.
- **2026-09-03** — **T1 (#1) built + verified**: FastAPI walking skeleton under `backend/` — `GET /health` (DB reachability), pytest+httpx harness over an ephemeral pgvector container, model-gateway seam + deterministic fake, modular monolith with import-linter-enforced boundaries. Gate green: ruff, pyright (0 errors), 5/5 tests, 1/1 import contract.
- **2026-09-03** — **T2 (#2) built + verified**: passage store (`core/store.py`, pgvector + HNSW, idempotent upsert) + corpus ingestion CLI (markdown front-matter + PDF via pypdf, structure-aware chunking, batched embedding through the gateway). Real embedder = local sentence-transformers (optional `embeddings` extra, lazy); tests use FakeGateway over real pgvector. Gate green: ruff, pyright, **10/10 tests**, import contract kept. Committed to `dev`. (JSON/PLOS reader deferred; markdown+PDF cover the pipeline.)
- **2026-09-03** — **T3 (#3) built + verified**: `retrieval.retrieve` (embed query → top-k cosine over pgvector HNSW, `core/store.search`) + `chat.answer` (retrieve → synthesize grounded `Answer` with citations that resolve to retrieved passages) + `POST /chat` wired (was 501). Real synthesis = LiteLLM via optional `synthesis` extra (lazy); tests use FakeGateway over real pgvector at the HTTP seam. Gate green: ruff, pyright, **12/12 tests**, import contract kept. **Frontier now: #4 (T4)** — Insufficient Context + no-fabrication (both #4 and #5 unblocked; parallel). Note: T3 has a minimal zero-passage → insufficient guard that T4 replaces with the real grounding-threshold policy.
- **2026-09-04** — Promoted `dev` → `main` → `prod` (all three hold identical T1–T3 content). **T4 (#4) built + verified**: grounding-threshold filter in `chat.answer` (below-threshold ⇒ Insufficient Context, synthesis skipped); no-fabrication holds by construction (citations built only from retrieved passages) — asserted by test. FakeGateway upgraded to token-overlap embeddings so retrieval ordering is meaningful. Gate green: ruff, pyright, **16/16 tests**, import contract kept. **Frontier now: #5 (T5)** — one Langfuse trace per Query (the last M1 ticket).
- **2026-09-04** — **T5 (#5) built + verified**: tracing seam (`core/observability.py` — Tracer/Trace protocol, NullTracer default, RecordingTracer for tests, lazy LangfuseTracer via optional `tracing` extra) wrapping `chat.answer`; one trace per Query with a `retrieve` span and a `synthesize` span only when grounded. Gate green: ruff, pyright, **18/18 tests**, import contract kept. **M1 COMPLETE (5/5).** Promoted `dev` → `main` → `prod`. **Next milestone: M2** (full contracts & storage) — or wire a frontend (M8, decision open). Real embed/synthesis/tracing need their extras + backends for a live run.

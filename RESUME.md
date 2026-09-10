# RESUME — Psychology Maverick (backend build)

**The single place to resume from.** Last worked: **2026-09-07**. Read this top-to-bottom, then §11 is the exact next action.

> Also loaded automatically next session: the project memory at
> `~/.claude/projects/-Users-kaalabhairava-AgenticAIApplication/memory/` (auto-injects a summary).
> This file is the human-readable source of truth; `docs/ROADMAP.md` is the live milestone tracker.

---

## 0. Resume in 30 seconds

- **What:** a retrieval-grounded, citation-first AI assistant for psychology / mental health. Informational-only, crisis-first. Portfolio-grade production stack ("the engineering around the LLM is the point").
- **Where the work is:** `~/AgenticAIApplication/backend/` (FastAPI modular monolith). *(The earlier design/prototype lives elsewhere — see §9.)*
- **Progress:** **M1 ✅ · M2 ✅ · M3 ✅ · M4 ✅ · M5 ✅** of a 9-milestone plan. **54/54 tests green.**
- **Branches:** `main`/`prod` = M1–M4 (`78532d7`/`0819a95`). `dev` = M1–M5 (`15ef8ff`). **`dev` is ahead of `main`/`prod` by all of M5 — not yet promoted.**
- **Next:** **M6 — Auth & security** (email+password JWT, RBAC, per-User conversation ownership). See §11.

---

## 1. What this is

Psychology Maverick answers questions about **psychology, psychiatry, and mental health** strictly from a
curated, openly-licensed **Corpus**, **citing every claim**. It is **informational only** (never diagnosis
or personalized advice) and **crisis-first** (a query signalling acute risk gets support resources, never a
corpus answer). Glossary is authoritative: **Query, Answer, Corpus, Citation, Category, Insufficient Context,
Faithfulness, User, Admin, Crisis Escalation** — see [CONTEXT.md](CONTEXT.md); use these terms, avoid the
listed synonyms.

Product truth: [PRODUCT.md](PRODUCT.md) · [project.md](project.md) · PRD in [docs/PRD.md](docs/PRD.md).
Decisions: [docs/adr/](docs/adr/) (0001 single-postgres-pgvector · 0002 config-driven model gateway ·
0003 hybrid deployment · 0004 informational safety posture *(non-negotiable)* · 0005 modular monolith /
vertical slices · 0006 deep-module seams).

---

## 2. Status — the 9 milestones

Live tracker: [docs/ROADMAP.md](docs/ROADMAP.md). Each milestone = a spec (`docs/specs/`) → `ready-for-agent`
GitHub tickets → build ticket-by-ticket → promote.

| M | Milestone | Status | Spec |
|---|-----------|:---:|---|
| **M1** | Vertical slice: ingest → real `/chat` (retrieve→synthesize) → trace | ✅ | `docs/specs/M1-rag-chat-slice.md` |
| **M2** | Contracts & storage: `Answer` invariants, Category on every passage, JSON reader, corpus stats | ✅ | `docs/specs/M2-contracts-and-storage.md` |
| **M3** | Agent: LangGraph graph + Postgres checkpointer + multi-turn + keyword tool | ✅ | `docs/specs/M3-agent.md` |
| **M4** | **Safety**: crisis node, faithfulness judge, HITL interrupt, disclaimers (ADR-0004) | ✅ | `docs/specs/M4-safety.md` |
| **M5** | Model gateway: LiteLLM registry, role routing + fallback | ✅ | `docs/specs/M5-model-gateway.md` |
| **M6** | Auth & security: JWT, RBAC, per-User conversation ownership | ⬜ **next** | — |
| **M7** | Evals suite + CI quality gate | ⬜ | — |
| **M8** | Frontend: chat + citations + trust states + auth + sidebar | ⬜ | — |
| **M9** | Deploy: Render + Neon + Upstash + Vercel + Langfuse | ⬜ | — |

All M1–M5 tickets (#1–#5, #7–#9, #10–#12, #13–#16, #17–#19) are **closed**. GitHub:
`https://github.com/PrasannaMalatesha/psychology-maverick` (public). Branching PR #6 merged.

---

## 3. Run & test the backend

```bash
cd ~/AgenticAIApplication/backend
uv sync                         # deps (Python 3.13 + uv)
uv run pytest                   # 38 tests — needs Docker running (ephemeral pgvector via testcontainers)
uv run pyright                  # 0 errors
uv run ruff check               # lint
uv run lint-imports             # module-boundary contract (ADR-0005/0006)
```

The full gate that must stay green: **ruff · pyright · pytest · import-linter**.

Run the API (needs a database):
```bash
docker compose up -d db         # Postgres+pgvector on :5432 (or use Neon)
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/maverick
uv run uvicorn app.main:app --reload
# ingest a corpus subset:
uv run python -m app.features.corpus.cli ingest <dir>
uv run python -m app.features.corpus.cli stats
```

**Real models are optional extras** (tests use a deterministic `FakeGateway`, so CI needs none):
`uv sync --extra embeddings` (local bge-small via sentence-transformers) ·
`--extra synthesis` (LiteLLM; needs an LLM API key) · `--extra tracing` (Langfuse).

**Live run done once (2026-09-06):** real bge + real pgvector retrieval works end to end; synthesis was
stubbed (no LLM key). Finding: bge-small's similarity floor is high → default `grounding_threshold` set to
**0.5** (M2·T2). ⚠️ **A leftover dev container `mav-live` (pgvector on :5434) may still be running — tear it
down: `docker rm -f mav-live`.**

---

## 4. Architecture (as built)

Modular monolith (ADR-0005), deep modules with small interfaces (ADR-0006). Boundaries enforced by
import-linter: **`chat` > `assistant` > `retrieval` > `corpus`**; shared contracts live in `core`.

```
backend/app/
  core/
    config.py        Settings (DATABASE_URL, retrieval_top_k=5, grounding_threshold=0.5, model roles, chunk sizes)
    db.py            engine, ensure_pgvector, check_health
    contracts.py     Register, Category, AnswerState, Citation, Answer (self-validating), Query   <-- shared contract
    store.py         Passage model (pgvector 384 + HNSW), replace_passages (idempotent, orphan-free),
                     search (semantic top-k), keyword_search (ILIKE), corpus_stats
    checkpoint.py    make_postgres_checkpointer (LangGraph Postgres saver; setup() creates tables)
    observability.py Tracer/Trace protocol; NullTracer, RecordingTracer, LangfuseTracer (lazy)
    llm/
      gateway.py         ModelGateway protocol (embed, synthesize), EMBEDDING_DIM=384
      fake_gateway.py    FakeGateway — token-overlap embeddings (deterministic; the ONE test stub)
      production_gateway.py  bge embeddings (sentence-transformers, lazy) + LiteLLM synthesis (lazy)
  features/
    corpus/     documents.py (md/txt front-matter + PDF via pypdf; JSON = title manifest),
                chunking.py (structure-aware, overlap, stable ids), service.py (ingest), cli.py (ingest|stats)
    retrieval/  service.py: RetrievalService.retrieve (semantic) + .keyword (ILIKE, score 1.0)
    assistant/  agent.py (LangGraph StateGraph: retrieve → grade → keyword_tool? → synthesize; JSON-plain
                state; trace spans via run config), service.py (compile w/ checkpointer, answer, history)
    chat/       service.py (ChatService delegates to assistant; MemorySaver default), router.py
                (POST /chat + optional conversation_id + X-Conversation-Id header; GET /conversations/{id}),
                schemas.py (re-exports the contract from core.contracts)
  main.py       create_app(settings, gateway, tracer, checkpointer) — all injectable; module-level `app`
tests/          pgvector-backed (testcontainers, Ryuk disabled on macOS), FakeGateway stub;
                fixtures/corpus/{textbooks,articles,mental_health}/*.md
```

**Behavior today:** a Query flows ingest → embed → **retrieve** (semantic top-k over pgvector/HNSW) →
**grade** (if nothing clears the threshold → **keyword_tool** ILIKE escape hatch) → **synthesize** a grounded,
cited `Answer` **or Insufficient Context** (grounded-or-silent) → one trace per query → multi-turn via the
checkpointer (`conversation_id`). No-fabrication holds by construction (citations are built only from
retrieved passages). The `Answer` model self-validates its shape.

---

## 5. Repo, branching, GitHub

- **Three long-lived branches** (documented in [CLAUDE.md](CLAUDE.md)): **`dev`** (all development lands here) →
  **`main`** (stable trunk) → **`prod`** (deploy). Never commit features to main/prod.
- Promote with merges (non-destructive): `git checkout main && git merge dev && git push` then
  `git checkout prod && git merge main && git push` then `git checkout dev`.
- **`dev` is currently ahead of `main`/`prod` by all of M5.** Promote when ready (`main`/`prod` are at M4).
- `gh` is authenticated as **PrasannaMalatesha**. Corpus PDFs are gitignored (reproducible via
  `data/fetch_corpus.sh`); commits carry no AI-attribution trailers (house rule).
- **Note:** `gh issue close` sometimes shows the issue still open for a few seconds (API read-lag) — the close
  succeeds; re-check after a moment.

---

## 6. The workflow (repeat per milestone)

`/spec` (or write the spec doc) → `/to-tickets` (publish `ready-for-agent` GitHub issues, blockers wired) →
build each ticket on `dev` (tracer-bullet vertical slices) → `/code-review` per milestone → gate green →
commit + close the issue → promote `dev→main→prod`. Update `docs/ROADMAP.md` and memory as you go.

Matt-Pocock skill config lives in `docs/agents/` (issue tracker = GitHub; the five triage labels exist;
domain docs = single-context). Set up via `/setup-matt-pocock-skills`.

---

## 7. Skills & tools in play (re-engage next session)

Global defaults auto-load from `~/.claude/CLAUDE.md`: **caveman** (terse prose), **ponytail** (write-less
overlay — on for coding; keep it on), **feature-dev**, **impeccable**, **refero-design**, **gstack** suite,
**claude-mem** (session memory). Used this build:

- **Matt-Pocock engineering skills** — `/spec`, `/to-tickets`, `/code-review`, `/setup-matt-pocock-skills`.
- **`/codebase-design`** — deep-module vocabulary → ADR-0006.
- **`/implement`** — the build-then-review-then-commit loop (used for T1s).
- **`/ponytail`** — kept scope lazy (e.g., flagged LangGraph weight; JSON-plain graph state; no premature abstractions).
- **`/code-review`** — two-axis reviews (run inline for this self-authored backend rather than spawning cloud agents).

Design-side skills (from the earlier prototype work, if the frontend is picked up at M8): `impeccable`,
`design-taste-frontend`, `animate`, `emil-design-eng`, `/design`. See §9.

Toolchain: **Python 3.13 + uv**; Docker (pgvector via testcontainers); `gh` CLI. Neon pgvector MCP is
available in-session for a real DB without Docker.

---

## 8. Open decisions & deferred items

- **Frontend target (blocks M8):** the ADRs assume a **Next.js** app on the **MindMarket** design system
  (this repo's `design/`). A polished **fork** exists at `~/Downloads/Figma_Design_Files/_extracted/`
  (Vite/React, DM fonts, its own `RESUME.md`). Decide whether M8 builds canonical or adopts the fork. The
  M1–M7 backend is frontend-agnostic, so it does not block them.
- **Deferred to M7 (evals):** a real per-passage **Category** classifier (today it's a coarse per-register
  default); final **grounding_threshold** calibration against the real corpus.
- **Deploy-time (M9):** wire **PostgresSaver** as the app checkpointer (default is MemorySaver); pin/adapt
  **langfuse** (LangfuseTracer targets v2 API; the extra can resolve to v3); provision Neon/Upstash/Langfuse/
  Render/Vercel (owner's task).

---

## 9. The other artifact (design/frontend)

Two Psychology Maverick codebases exist:
- **This one (canonical):** `~/AgenticAIApplication` — the real product + backend (M1–M3 here). Design system
  = **MindMarket** (Bricolage/Inter/JetBrains Mono, paper-cut mascot); 11-screen HTML prototype in
  `design/prototype/`; e2e 46/46.
- **The fork:** `~/Downloads/Figma_Design_Files/_extracted/` — a polished Figma-Make React export (DM fonts,
  green-smiley mascot) with its own feature-rich UI (DSM-5 answers, legal pages, freemium, editorial
  redesign, responsive drawer, WCAG-AA pass). Has its own `RESUME.md`. **Kept as a fork by choice.**
The fork-vs-canonical frontend decision is the M8 fork above.

---

## 10. Gotchas

- Tests need **Docker running**; macOS + testcontainers requires `TESTCONTAINERS_RYUK_DISABLED=true` (already set in conftest).
- The `Bash` tool's cwd resets between calls — use absolute paths / `cd` inside each command.
- FakeGateway embeddings are **token-overlap**, not semantic — tests assert structure/threading/routing, not answer quality (that's M7). Threshold branches are tested by controlling the threshold value, not the fake's magnitudes.
- `Citation` serializes its register field as the alias **`register`** (glossary term); the Python attribute is `source_register`.
- LangGraph nodes must type their config param as `RunnableConfig` or LangGraph won't inject it.
- Tear down the leftover `mav-live` container (§3).

---

## 11. EXACT NEXT STEP

**M4 and M5 are done.** M4 (ADR-0004 safety gate) is on `main`/`prod`. M5 (config-driven model gateway,
ADR-0002) is committed on `dev` (`15ef8ff`, issues #17–#19 closed): `ProductionGateway` is now a role
registry — `ModelRole` primary+fallback chains for `synthesizer`/`judge`/`embedder` in `Settings`, one
`_complete` router, embedder `local/<id>` vs LiteLLM embeddings with an `EMBEDDING_DIM` guard. `grader`
omitted (no LLM grader). 54/54 tests. See `docs/specs/M5-model-gateway.md`.

**Start M6 (Auth & security).** Scope (project.md §15.6): email+password JWT (argon2, refresh-token
rotation, Redis revocation), user/admin RBAC, and per-User conversation ownership (today `GET
/conversations/{id}` and the review endpoint are unauthenticated — M6 puts them behind ownership).

Kick off exactly as M2–M5: write `docs/specs/M6-auth-security.md` → `/to-tickets` → build on `dev` → gate → promote.
Say **"start M6"** (or **"promote first"** to push M5 → `main`/`prod` before M6). Everything above is committed on `dev`.
